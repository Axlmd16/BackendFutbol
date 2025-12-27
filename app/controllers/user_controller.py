"""Controlador de usuarios - maneja la lógica de negocio de usuarios del club."""

import logging

from sqlalchemy.orm import Session

from app.client.person_ms_service import PersonMSService
from app.dao.account_dao import AccountDAO
from app.dao.user_dao import UserDAO
from app.schemas.user_schema import (
    AdminCreateUserRequest,
    AdminCreateUserResponse,
    AdminUpdateUserRequest,
    AdminUpdateUserResponse,
    CreatePersonInMSRequest,
    UserDetailResponse,
    UserFilter,
)
from app.utils.exceptions import AlreadyExistsException, ValidationException
from app.utils.security import hash_password, validate_ec_dni

logger = logging.getLogger(__name__)


class UserController:
    """
    Controlador de usuarios del sistema (club).
    """

    def __init__(self) -> None:
        self.user_dao = UserDAO()
        self.account_dao = AccountDAO()
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
        dni = validate_ec_dni(payload.dni)

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
        """
        if self.user_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("Ya existe un usuario con ese DNI en el club")

        if self.account_dao.exists(db, "email", email):
            raise AlreadyExistsException(
                "Ya existe una cuenta con ese email en el club"
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

        print("PERSON DATA:", person_data)
        nombre = person_data["data"]["firts_name"]

        print(f"nombre: {nombre}")

        return UserDetailResponse(
            id=user.id,
            full_name=user.full_name,
            role=user.account.role.value,
            dni=user.dni,
            email=user.account.email,
            external=user.external,
            is_active=user.is_active,
            first_name=person_data["data"]["firts_name"],
            last_name=person_data["data"]["last_name"],
            direction=person_data["data"]["direction"],
            phone=person_data["data"]["phono"],
            type_identification=person_data["data"]["type_identification"],
            type_stament=person_data["data"]["type_stament"],
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
