"""Controlador de usuarios - maneja la lógica de negocio de usuarios del club."""

import logging

from sqlalchemy.orm import Session

from app.client.person_ms_service import PersonMSService
from app.dao.account_dao import AccountDAO
from app.dao.athlete_dao import AthleteDAO
from app.dao.user_dao import UserDAO
from app.models.enums.rol import Role
from app.schemas.user_schema import (
    AdminCreateUserRequest,
    AdminCreateUserResponse,
    AdminUpdateUserRequest,
    AdminUpdateUserResponse,
    CreatePersonInMSRequest,
    InternFilter,
    InternResponse,
    PromoteAthleteRequest,
    PromoteAthleteResponse,
    UserDetailResponse,
    UserFilter,
)
from app.utils.dni_validator import validate_dni_not_exists_locally
from app.utils.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.utils.security import hash_password, validate_ec_dni

logger = logging.getLogger(__name__)


class UserController:
    """
    Controlador de usuarios del sistema (club).
    """

    def __init__(self) -> None:
        self.user_dao = UserDAO()
        self.account_dao = AccountDAO()
        self.athlete_dao = AthleteDAO()
        self.person_ms_service = PersonMSService()

    async def admin_create_user(
        self,
        db: Session,
        payload: AdminCreateUserRequest,
        requester_account_id: int | None = None,
    ) -> AdminCreateUserResponse:
        """
        Crea un administrador o entrenador.

        Flujo:
        1. Validar datos y unicidad local
        2. Crear persona en MS de usuarios (o recuperar si ya existe)
        3. Guardar usuario y cuenta localmente
        """
        # Normalizar datos
        first_name = payload.first_name.strip()
        last_name = payload.last_name.strip()
        email = payload.email.strip().lower()

        # Solo validar como cédula ecuatoriana si el tipo es CEDULA
        if payload.type_identification == "CEDULA":
            dni = validate_ec_dni(payload.dni)
        else:
            # Para PASSPORT y RUC, el schema ya validó el formato
            dni = payload.dni

        # Validar unicidad en el club
        self._validate_user_uniqueness(db, dni=dni, email=email)

        # Crear o recuperar persona en MS de usuarios
        external = await self.person_ms_service.create_or_get_person(
            CreatePersonInMSRequest(
                first_name=first_name,
                last_name=last_name,
                dni=dni,
                direction=payload.direction,
                phone=payload.phone,
                type_identification=payload.type_identification,
                type_stament=payload.type_stament,
            )
        )

        # Crear usuario y cuenta localmente
        full_name = f"{first_name} {last_name}"
        user, account = self._create_local_user_and_account(
            db=db,
            external=external,
            full_name=full_name,
            dni=dni,
            email=email,
            password=payload.password,
            role=payload.role,
        )

        return AdminCreateUserResponse(
            id=user.id,
            account_id=account.id,
            full_name=full_name,
            email=email,
            role=account.role.value,
            external=external,
        )

    async def admin_update_user(
        self,
        db: Session,
        payload: AdminUpdateUserRequest,
        user_id: int,
    ) -> AdminUpdateUserResponse:
        """
        Actualiza un administrador o entrenador.

        Flujo:
        1. Verificar que el usuario existe
        2. Actualizar en MS de usuarios
        3. Actualizar localmente (incluyendo external si cambió)
        """
        # Verificar que el usuario existe
        user = self.user_dao.get_by_id(db=db, id=user_id, only_active=False)
        if not user:
            raise ValidationException("El usuario a actualizar no existe")

        # Actualizar en MS de usuarios (puede devolver nuevo external)
        new_external = await self.person_ms_service.update_person(
            external=user.external,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            dni=user.dni,
            direction=payload.direction,
            phone=payload.phone,
            type_identification=payload.type_identification,
            type_stament=payload.type_stament,
        )

        # Actualizar localmente
        update_data = {
            "full_name": f"{payload.first_name.strip()} {payload.last_name.strip()}",
            "external": new_external,
        }

        updated_user = self.user_dao.update(db, user.id, update_data)
        if not updated_user:
            raise ValidationException("Error al actualizar el usuario")

        return AdminUpdateUserResponse(
            id=updated_user.id,
            full_name=updated_user.full_name,
            email=updated_user.account.email,
            role=updated_user.account.role.value,
            updated_at=updated_user.updated_at,
            is_active=updated_user.is_active,
        )

    def _validate_user_uniqueness(self, db: Session, dni: str, email: str) -> None:
        """
        Valida que DNI y email no existan en el club.
        Verifica en usuarios, atletas y representantes.
        """
        # Validar DNI en todas las entidades locales ANTES de ir al MS externo
        validate_dni_not_exists_locally(db, dni)

        # Validar email único en cuentas
        if self.account_dao.exists(db, "email", email):
            raise AlreadyExistsException(
                "Ya existe una cuenta con ese email en el sistema"
            )

    def _create_local_user_and_account(
        self,
        db: Session,
        external: str,
        full_name: str,
        dni: str,
        email: str,
        password: str,
        role,
    ):
        """
        Crea usuario y cuenta en la base de datos local.
        """
        new_user = self.user_dao.create(
            db,
            {
                "external": external,
                "full_name": full_name,
                "dni": dni,
            },
        )

        new_account = self.account_dao.create(
            db,
            {
                "email": email,
                "password_hash": hash_password(password),
                "role": role,
                "user_id": new_user.id,
            },
        )

        return new_user, new_account

    def get_all_users(self, db: Session, filters: UserFilter):
        """
        Obtiene usuarios aplicando los filtros recibidos.
        """
        return self.user_dao.get_all_with_filters(db, filters=filters)

    async def get_user_by_id(
        self, db: Session, user_id: int
    ) -> UserDetailResponse | None:
        """
        Obtiene la informacion personal de un uusario
        """
        user = self.user_dao.get_by_id(db=db, id=user_id)
        if not user:
            return None

        # Obtener datos desde MS de personas
        person_data = await self.person_ms_service.get_user_by_identification(user.dni)
        if not person_data:
            raise ValidationException("No se encontró la información de la persona")

        # Manejar posibles typos del MS externo
        # (firts_name -> first_name, phono -> phone)
        data = person_data.get("data", {})
        first_name = data.get("first_name") or data.get("firts_name", "")
        last_name = data.get("last_name", "")
        phone = data.get("phone") or data.get("phono", "S/N")

        return UserDetailResponse(
            id=user.id,
            full_name=user.full_name,
            role=user.account.role.value,
            dni=user.dni,
            email=user.account.email,
            external=user.external,
            is_active=user.is_active,
            first_name=first_name,
            last_name=last_name,
            direction=data.get("direction", "S/N"),
            phone=phone,
            type_identification=data.get("type_identification", "CEDULA"),
            type_stament=data.get("type_stament", "EXTERNOS"),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def desactivate_user(self, db: Session, user_id: int) -> None:
        """
        Desactiva un usuario (soft delete).
        """
        user = self.user_dao.get_by_id(db=db, id=user_id)
        if not user:
            raise ValidationException("El usuario a desactivar no existe")

        self.user_dao.update(db, user_id, {"is_active": False})

    def activate_user(self, db: Session, user_id: int) -> None:
        """
        Activa un usuario (soft delete).
        """
        # Buscar incluyendo inactivos para poder activarlos
        user = self.user_dao.get_by_id(db=db, id=user_id, only_active=False)
        if not user:
            raise ValidationException("El usuario a activar no existe")

        self.user_dao.update(db, user_id, {"is_active": True})

    # ==========================================
    # MÉTODOS DE PASANTES (INTERNS)
    # ==========================================

    def promote_athlete_to_intern(
        self,
        db: Session,
        athlete_id: int,
        payload: PromoteAthleteRequest,
    ) -> PromoteAthleteResponse:
        """
        Promueve un atleta existente a pasante.

        Flujo:
        1. Verificar que el atleta existe
        2. Verificar que el atleta no tiene ya una cuenta
        3. Crear User usando el external_person_id del atleta
        4. Crear Account con role=INTERN
        """
        # Verificar que el atleta existe
        athlete = self.athlete_dao.get_by_id(db=db, id=athlete_id)
        if not athlete:
            raise NotFoundException("El atleta no existe")

        # Verificar que el atleta no tiene ya una cuenta
        existing_user = self.user_dao.get_by_field(db, "dni", athlete.dni)
        if existing_user:
            raise AlreadyExistsException(
                "Este atleta ya tiene una cuenta en el sistema"
            )

        # Verificar que el email no esté en uso
        email = payload.email.strip().lower()
        if self.account_dao.exists(db, "email", email):
            raise AlreadyExistsException("Ya existe una cuenta con ese email")

        # Crear usuario usando el external_person_id del atleta
        new_user = self.user_dao.create(
            db,
            {
                "external": athlete.external_person_id,
                "full_name": athlete.full_name,
                "dni": athlete.dni,
            },
        )

        # Crear cuenta con rol INTERN
        new_account = self.account_dao.create(
            db,
            {
                "email": email,
                "password_hash": hash_password(payload.password),
                "role": Role.INTERN,
                "user_id": new_user.id,
            },
        )

        return PromoteAthleteResponse(
            id=new_account.id,
            user_id=new_user.id,
            full_name=athlete.full_name,
            email=email,
            role=Role.INTERN.value,
        )

    def get_all_interns(
        self, db: Session, filters: InternFilter
    ) -> tuple[list[InternResponse], int]:
        """
        Obtiene todos los pasantes con paginación y búsqueda.
        """
        users, total = self.user_dao.get_interns_with_filters(db, filters=filters)

        interns = []
        for user in users:
            # Buscar el atleta correspondiente por DNI
            athlete = self.athlete_dao.get_by_field(db, "dni", user.dni)
            athlete_id = athlete.id if athlete else 0

            interns.append(
                InternResponse(
                    id=user.account.id,
                    user_id=user.id,
                    full_name=user.full_name,
                    dni=user.dni,
                    email=user.account.email,
                    athlete_id=athlete_id,
                    is_active=user.is_active,
                    created_at=user.created_at,
                )
            )

        return interns, total

    def deactivate_intern(self, db: Session, account_id: int) -> None:
        """
        Desactiva un pasante (soft delete).
        """
        account = self.account_dao.get_by_id(db=db, id=account_id)
        if not account:
            raise NotFoundException("El pasante no existe")

        if account.role != Role.INTERN:
            raise ValidationException("El usuario no es un pasante")

        self.user_dao.update(db, account.user_id, {"is_active": False})

    def activate_intern(self, db: Session, account_id: int) -> None:
        """
        Activa un pasante.
        """
        account = self.account_dao.get_by_id(db=db, id=account_id)
        if not account:
            raise NotFoundException("El pasante no existe")

        if account.role != Role.INTERN:
            raise ValidationException("El usuario no es un pasante")

        self.user_dao.update(db, account.user_id, {"is_active": True})
