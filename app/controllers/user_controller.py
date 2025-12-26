"""Controlador de usuarios del sistema (club)."""

import logging

from sqlalchemy.orm import Session

from app.client.person_client import PersonClient
from app.dao.account_dao import AccountDAO
from app.dao.user_dao import UserDAO
from app.models.account import Account
from app.models.enums.rol import Role
from app.schemas.user_schema import AdminCreateUserRequest, AdminCreateUserResponse
from app.utils.exceptions import (
    AlreadyExistsException,
    DatabaseException,
    UnauthorizedException,
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

    def _ensure_requester_is_admin(
        self, db: Session, requester_account_id: int
    ) -> Account:
        """Valida que quien llama sea administrador del club."""
        requester = self.account_dao.get_by_id(
            db, requester_account_id, only_active=True
        )
        if not requester:
            raise UnauthorizedException("Cuenta solicitante no encontrada o inactiva")
        if requester.role != Role.ADMINISTRATOR:
            raise UnauthorizedException(
                "Solo el administrador puede realizar esta acción"
            )
        return requester

    async def admin_create_user(
        self,
        db: Session,
        payload: AdminCreateUserRequest,
        requester_account_id: int | None = None,
    ) -> AdminCreateUserResponse:
        """Crea un admin/entrenador en el MS de usuarios y lo enlaza al club."""

        # TODO: habilitar validación de admin despues con auth
        # if requester_account_id is not None:
        #     self._ensure_requester_is_admin(db, requester_account_id)

        first_name = payload.first_name.strip()
        last_name = payload.last_name.strip()
        email = payload.email.strip().lower()
        dni = validate_ec_dni(payload.dni)
        role_str = payload.role.strip().lower()

        if not first_name or not last_name:
            raise ValidationException("Nombre y apellidos son requeridos")

        if role_str in ("administrador", "administrator", "admin"):
            role_enum = Role.ADMINISTRATOR
        elif role_str in ("entrenador", "coach"):
            role_enum = Role.COACH
        else:
            raise ValidationException(
                "Rol inválido. Use 'administrador' o 'entrenador'"
            )

        if self.user_dao.exists(db, "dni", dni):
            raise AlreadyExistsException(
                "Ya existe un usuario con ese DNI en el club"
            )

        if self.account_dao.exists(db, "email", email):
            raise AlreadyExistsException(
                "Ya existe una cuenta con ese email en el club"
            )

        person_payload = {
            "first_name": first_name,
            "last_name": last_name,
            "identification": dni,
            "type_identification": payload.type_identification,
            "type_stament": payload.type_stament,
            "direction": payload.direction or "S/N",
            "phono": payload.phone or "S/N",
            "email": email,
            "password": payload.password,
        }

        def _is_duplicate_person_message(raw_message: str | None) -> bool:
            msg = (raw_message or "").lower()
            # Solo intentamos enlazar si el MS indica que
            # la persona ya existe por identificación/DNI.
            return (
                ("persona" in msg or "identificaci" in msg or "dni" in msg)
                and ("ya existe" in msg or "duplic" in msg)
            )

        async def _fetch_existing_external() -> tuple[str, str]:
            try:
                person_data = await self.person_client.get_by_identification(dni)
            except Exception as exc:  # pragma: no cover - log para trazabilidad
                logger.error(
                    (
                        "No se pudo consultar persona existente en MS usuarios "
                        "por DNI %s: %s"
                    ),
                    dni,
                    exc,
                )
                raise ValidationException(
                    (
                        "La persona ya existe en el módulo de usuarios, pero no "
                        "se pudo recuperar su identificador externo"
                    )
                ) from exc

            data_block = person_data.get("data") or {}
            external = data_block.get("external")
            if not external:
                raise ValidationException(
                    (
                        "La persona ya existe en el módulo de usuarios, pero la "
                        "respuesta no contiene el identificador externo"
                    )
                )
            # MS no retorna account_id por separado, usamos el mismo external
            return external, external

        try:
            save_resp = await self.person_client.create_person_with_account(
                person_payload
            )
        except Exception as exc:
            logger.error(f"Error al llamar a save-account en MS usuarios: {exc}")
            raise ValidationException(
                "No se pudo registrar la persona en el sistema institucional"
            ) from exc

        if save_resp.get("status") != "success":
            message = save_resp.get("message") or save_resp.get("detail") or ""
            if _is_duplicate_person_message(message):
                (
                    external_person_id,
                    external_account_id,
                ) = await _fetch_existing_external()
            else:
                raise ValidationException(
                    f"Error desde MS de usuarios: {message or 'Error desconocido'}"
                )
        else:
            try:
                person_data = await self.person_client.get_by_identification(dni)
            except Exception as exc:
                logger.error(
                    f"Error al obtener persona por DNI en MS usuarios: {exc}"
                )
                raise ValidationException(
                    (
                        "La persona se creó pero no se pudo recuperar del "
                        "sistema institucional"
                    )
                ) from exc

            person = person_data.get("data") or {}
            external_person_id = person.get("external")
            external_account_id = person.get("external")

            if not external_person_id:
                raise ValidationException(
                    "El MS de usuarios no devolvió external_id de la persona"
                )

        full_name = f"{first_name} {last_name}"

        try:
            new_user = self.user_dao.create(
                db,
                {
                    "external": external_person_id,
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
        except DatabaseException as exc:
            logger.error(
                f"Error al crear registros locales de usuario/cuenta: {exc}"
            )
            raise

        return AdminCreateUserResponse(
            user_id=new_user.id,
            account_id=new_account.id,
            external_person_id=external_person_id,
            external_account_id=external_account_id,
            full_name=full_name,
            email=email,
            role=new_account.role.value,
        )
