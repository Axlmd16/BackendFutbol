# app/controllers/user_controller.py
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
    UnauthorizedException,
    ValidationException,
    DatabaseException,
)
from app.utils.security import validate_ec_dni

logger = logging.getLogger(__name__)

class UserController:
    """Controlador de usuarios del sistema (club)."""

    def __init__(self) -> None:
        self.user_dao = UserDAO()
        self.account_dao = AccountDAO()
        self.person_client = PersonClient()

    def _ensure_requester_is_admin(self, db: Session, requester_account_id: int) -> Account:
        """Valida que quien llama sea administrador del club."""
        requester = self.account_dao.get_by_id(db, requester_account_id, only_active=True)
        if not requester:
            raise UnauthorizedException("Cuenta solicitante no encontrada o inactiva")
        if requester.role != Role.ADMINISTRATOR:
            raise UnauthorizedException("Solo el administrador puede realizar esta acción")
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
        last_name  = payload.last_name.strip()
        email      = payload.email.strip().lower()
        dni        = validate_ec_dni(payload.dni)
        role_str   = payload.role.strip().lower()

        if not first_name or not last_name:
            raise ValidationException("Nombre y apellidos son requeridos")

        # Mapear string al Rol
        if role_str in ("administrador", "administrator", "admin"):
            role_enum = Role.ADMINISTRATOR
        elif role_str in ("entrenador", "coach"):
            role_enum = Role.COACH
        else:
            raise ValidationException("Rol inválido. Use 'administrador' o 'entrenador'")

        # Evitar duplicados locales (en el club)
        if self.user_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("Ya existe un usuario con ese DNI en el club")

        # Crear persona + cuenta en el MS de usuarios
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

        try:
            save_resp = await self.person_client.create_person_with_account(person_payload)
        except Exception as e:
            logger.error(f"Error al llamar a save-account en MS usuarios: {e}")
            raise ValidationException("No se pudo registrar la persona en el sistema institucional")

        if save_resp.get("status") != "success":
            raise ValidationException(f"Error desde MS de usuarios: {save_resp.get('message')}")

        # 2) Recuperar datos de la persona para obtener external_id de persons y accounts
        try:
            person_data = await self.person_client.get_by_identification(dni)
        except Exception as e:
            logger.error(f"Error al obtener persona por DNI en MS usuarios: {e}")
            raise ValidationException("La persona se creó pero no se pudo recuperar del sistema institucional")

        person = person_data.get("data") or {}
        external_person_id = person.get("external") 
        external_account_id = person.get("external") 

        if not external_person_id:
            raise ValidationException("El MS de usuarios no devolvió external_id de la persona")

        full_name = f"{first_name} {last_name}"

        # 3) Guardar el enlace local en el club
        try:
            new_user = self.user_dao.create(db, {
                "external_person_id": external_person_id,
                "full_name": full_name,
                "dni": dni,
            })

            new_account = self.account_dao.create(db, {
                "external_account_id": external_account_id,
                "role": role_enum,
                "user_id": new_user.id,
            })
        except DatabaseException as e:
            logger.error(f"Error al crear registros locales de usuario/cuenta: {e}")
            # TODO: si quieres, intentar borrar la persona en el MS de usuarios
            raise

        # TODO: enviar email de bienvenida con credenciales

        return AdminCreateUserResponse(
            user_id=new_user.id,
            account_id=new_account.id,
            external_person_id=external_person_id,
            external_account_id=external_account_id,
            full_name=full_name,
            email=email,
            role=new_account.role.value,
        )
