# app/controllers/user_controller.py
import logging
import random

from sqlalchemy.orm import Session

from app.client.person_client import PersonClient
from app.dao.account_dao import AccountDAO
from app.dao.user_dao import UserDAO
from app.schemas.user_schema import (
    AdminCreateUserRequest,
    AdminCreateUserResponse,
    AdminUpdateUserRequest,
    AdminUpdateUserResponse,
    CreateLocalUserAccountRequest,
    CreatePersonInMSRequest,
)
from app.utils.exceptions import (
    AlreadyExistsException,
    DatabaseException,
    ValidationException,
)
from app.utils.security import hash_password, validate_ec_dni

logger = logging.getLogger(__name__)


class UserController:
    """Controlador de usuarios del sistema (club)."""

    def __init__(self) -> None:
        self.user_dao = UserDAO()
        self.account_dao = AccountDAO()
        self.person_client = PersonClient()

    async def create_person_in_users_ms(
        self,
        data: CreatePersonInMSRequest,
    ) -> None:
        """Crea la persona en el MS de usuarios.

        Es idempotente: si la persona ya existe, no falla.
        """

        person_payload = {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "identification": data.dni,
            "type_identification": data.type_identification,
            "type_stament": data.type_stament,
            "direction": data.direction or "S/N",
            "phono": data.phone or "S/N",
            "email": f"user{random.randint(10000, 99999)}@example.com",
            "password": f"Pass{random.randint(10000, 99999)}!",
        }

        try:
            save_resp = await self.person_client.create_person_with_account(
                person_payload
            )
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error inesperado al llamar a MS de usuarios: {e}")
            raise ValidationException(
                "Error de comunicación con el módulo de usuarios"
            ) from e

        status = save_resp.get("status")
        message = save_resp.get("message", "").lower()

        if status == "success":
            return

        if (
            "ya existe" in message
            or "already exists" in message
            or "duplicad" in message
        ):
            logger.info(
                f"Persona con DNI {data.dni} ya existe en MS usuarios, continuando..."
            )
            return

        raise ValidationException(
            save_resp.get("message", "Error desconocido al crear persona")
        )

    async def update_person_in_users_ms(
        self,
        data: CreatePersonInMSRequest,
    ) -> None:
        """Actualiza la persona en el MS de usuarios.

        Es idempotente: si la persona no existe, no falla.
        """
        person_payload = {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "identification": data.dni,
            "type_identification": data.type_identification,
            "type_stament": data.type_stament,
            "direction": data.direction or "S/N",
            "phono": data.phone or "S/N",
        }

        try:
            update_resp = await self.person_client.update_person_by_dni(
                data.dni, person_payload
            )
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error inesperado al llamar a MS de usuarios: {e}")
            raise ValidationException(
                "Error de comunicación con el módulo de usuarios"
            ) from e

        status = update_resp.get("status")
        message = update_resp.get("message", "").lower()

        if status == "success":
            return

        if "no existe" in message or "does not exist" in message:
            logger.info(
                f"Persona con DNI {data.dni} no existe en MS usuarios, continuando..."
            )
            return

        raise ValidationException(
            update_resp.get("message", "Error desconocido al actualizar persona")
        )

    def create_local_user_account(
        self,
        db: Session,
        data: CreateLocalUserAccountRequest,
    ):
        """Crea el usuario y cuenta localmente en este MS."""

        dni = validate_ec_dni(data.dni)

        # Validar unicidad local
        if self.user_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("Ya existe un usuario con ese DNI en el club")
        if self.account_dao.exists(db, "email", data.email):
            raise AlreadyExistsException(
                "Ya existe una cuenta con ese email en el club"
            )

        # Crear usuario
        new_user = self.user_dao.create(
            db,
            {
                "full_name": data.full_name,
                "dni": dni,
            },
        )

        # Crear cuenta
        new_account = self.account_dao.create(
            db,
            {
                "email": data.email,
                "password_hash": hash_password(data.password),
                "role": data.role,
                "user_id": new_user.id,
            },
        )

        return new_user, new_account

    async def admin_create_user(
        self,
        db: Session,
        payload: AdminCreateUserRequest,
    ) -> AdminCreateUserResponse:
        """Crea un admin/entrenador en el MS de usuarios y lo enlaza al club."""

        first_name = payload.first_name.strip()
        last_name = payload.last_name.strip()
        email = payload.email.strip().lower()
        dni = validate_ec_dni(payload.dni)
        role_enum = payload.role

        # Validar unicidad local
        if self.user_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("Ya existe un usuario con ese DNI en el club")
        if self.account_dao.exists(db, "email", email):
            raise AlreadyExistsException(
                "Ya existe una cuenta con ese email en el club"
            )

        # Crear persona en el MS de usuarios (idempotente)
        await self.create_person_in_users_ms(
            CreatePersonInMSRequest(
                first_name=first_name,
                last_name=last_name,
                dni=dni,
                direction=payload.direction or "S/N",
                phone=payload.phone or "S/N",
                type_identification=payload.type_identification,
                type_stament=payload.type_stament,
            )
        )

        # Guardar el usuario y cuenta localmente
        full_name = f"{first_name} {last_name}"
        try:
            new_user = self.user_dao.create(
                db,
                {
                    "full_name": full_name,
                    "dni": dni,
                },
            )

            new_account = self.account_dao.create(
                db,
                {
                    "email": email,
                    "password_hash": hash_password(payload.password),
                    "role": role_enum,
                    "user_id": new_user.id,
                },
            )
        except DatabaseException as e:
            logger.error(f"Error al crear registros locales de usuario/cuenta: {e}")
            raise

        return AdminCreateUserResponse(
            user_id=new_user.id,
            account_id=new_account.id,
            full_name=full_name,
            email=email,
            role=new_account.role.value,
        )

    def admin_update_user(
        self,
        db: Session,
        payload: AdminUpdateUserRequest,
    ) -> AdminUpdateUserResponse:  # noqa: F821
        """Actualiza un admin/entrenador en el MS de usuarios y localmente."""

        # Verificar que el usuario exista
        user = self.user_dao.exists(db=db, field="id", value=payload.user_id)
        if not user:
            raise ValidationException("El usuario a actualizar no existe")

        # Actualizar campos del usuario
        update_data = {
            "full_name": payload.full_name.strip(),
        }

        self.user_dao.update(db, user, update_data)

        return AdminUpdateUserResponse(
            user_id=user.id,
            full_name=user.full_name,
            email=user.account.email,
            role=user.account.role.value,
            updated_at=user.updated_at,
            is_active=user.is_active,
        )
