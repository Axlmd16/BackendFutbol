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
    ) -> str:
        """Crea la persona en el MS de usuarios.

        Es idempotente: si la persona ya existe, no falla.
        """

        def _is_duplicate_message(raw_message: str) -> bool:
            msg = (raw_message or "").strip().lower()
            return (
                "la persona ya esta registrada con esa identificacion" in msg
                or "la persona ya está registrada con esa identificacion" in msg
                or ("ya existe una persona" in msg and "identific" in msg)
                or "already exists" in msg
                or "duplicad" in msg
            )

        def _extract_external(resp: object) -> str | None:
            if not isinstance(resp, dict):
                return None
            data_block = resp.get("data")
            if isinstance(data_block, dict):
                external = data_block.get("external")
                return str(external) if external else None
            if isinstance(data_block, list) and data_block:
                first = data_block[0]
                if isinstance(first, dict):
                    external = first.get("external")
                    return str(external) if external else None
            external = resp.get("external")
            return str(external) if external else None

        async def _get_existing_external_by_dni(dni: str) -> str:
            try:
                existing = await self.person_client.get_by_identification(dni)
            except Exception as e:
                logger.error(
                    f"No se pudo consultar persona existente en MS usuarios "
                    f"por DNI {dni}: {e}"
                )
                raise ValidationException(
                    (
                        "La persona ya existe en el módulo de usuarios, "
                        "pero no se pudo recuperar su identificador externo"
                    )
                ) from e

            external = _extract_external(existing)
            if not external:
                raise ValidationException(
                    "La persona ya existe en el módulo de usuarios, pero,"
                    "la respuesta no contiene el identificador externo"
                )
            return external

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
        except ValidationException as e:
            if _is_duplicate_message(getattr(e, "message", "") or str(e)):
                logger.info(
                    f"Persona con DNI {data.dni} ya existe en MS usuarios, continuando."
                )
                return await _get_existing_external_by_dni(data.dni)
            raise
        except Exception as e:
            logger.error(f"Error inesperado al llamar a MS de usuarios: {e}")
            raise ValidationException(
                "Error de comunicación con el módulo de usuarios"
            ) from e

        status = save_resp.get("status")
        raw_message = save_resp.get("message") or save_resp.get("detail") or ""
        message = str(raw_message).lower()

        if status == "success":
            external = _extract_external(save_resp)
            if external:
                return external
            return await _get_existing_external_by_dni(data.dni)

        if _is_duplicate_message(message):
            logger.info(
                f"Persona con DNI {data.dni} ya existe en MS usuarios, continuando..."
            )
            return await _get_existing_external_by_dni(data.dni)

        raise ValidationException(
            save_resp.get("message")
            or save_resp.get("detail")
            or "Error desconocido al crear persona"
        )

    async def create_local_user_account(
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
                "external": data.external,
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
        external = await self.create_person_in_users_ms(
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
                    "external": external,
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
            external=external,
        )
