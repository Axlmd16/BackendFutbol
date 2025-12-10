import logging

from sqlalchemy.orm import Session

from app.dao.account_dao import AccountDAO
from app.dao.user_dao import UserDAO
from app.models.account import Account
from app.models.enums.rol import Role
from app.schemas.user_schema import AdminCreateUserRequest, AdminCreateUserResponse
from app.utils.exceptions import AlreadyExistsException, UnauthorizedException, ValidationException, DatabaseException
from app.utils.security import (
    generate_secure_password,
    hash_password,
    is_email_allowed,
    normalize_role,
    validate_ec_dni,
    sanitize_email,
    sanitize_text,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserController:
    """Controlador de usuarios del sistema."""

    def __init__(self) -> None:
        self.user_dao = UserDAO()
        self.account_dao = AccountDAO()

    def _ensure_requester_is_admin(self, db: Session, requester_account_id: int) -> Account:
        """Valida que quien llama sea administrador root."""
        requester = self.account_dao.get_by_id(db, requester_account_id, only_active=True)
        if not requester:
            raise UnauthorizedException("Cuenta solicitante no encontrada o inactiva")
        if requester.role != Role.ADMINISTRATOR:
            raise UnauthorizedException("Solo el administrador raíz puede realizar esta acción")
        return requester

    def admin_create_user(
        self,
        db: Session,
        requester_account_id: int,
        payload: AdminCreateUserRequest
    ) -> AdminCreateUserResponse:
        """Crea un usuario y su cuenta"""

        requester = self._ensure_requester_is_admin(db, requester_account_id)

        first_name = sanitize_text(payload.nombres, max_length=100)
        last_name = sanitize_text(payload.apellidos, max_length=100)
        email = sanitize_email(payload.correo_institucional)
        dni = validate_ec_dni(payload.dni)
        role_normalized = normalize_role(payload.rol)

        # 3) Validaciones 
        if not first_name or not last_name:
            raise ValidationException("Nombre y apellidos son requeridos")

        if not dni or len(dni) < 6:
            raise ValidationException("DNI inválido")

        allowed_domains = settings.INSTITUTIONAL_EMAIL_DOMAINS or None
        if not is_email_allowed(email, allowed_domains):
            raise ValidationException("Correo institucional inválido o dominio no permitido")

        role_map = {
            "administrador": Role.ADMINISTRATOR,
            "administrator": Role.ADMINISTRATOR,
            "admin": Role.ADMINISTRATOR,
            "entrenador": Role.COACH,
            "coach": Role.COACH,
        }
        role_enum = role_map.get(role_normalized)
        if not role_enum:
            raise ValidationException("Rol inválido. Use administrador o entrenador")

        # 4) Verificar duplicados
        if self.user_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("Ya existe un usuario con ese DNI")
        if self.account_dao.exists(db, "email", email):
            raise AlreadyExistsException("Ya existe una cuenta con ese correo")

        # 5) Generar credenciales
        temp_password = generate_secure_password()
        hashed_password = hash_password(temp_password)

        # 6) Guadar el usaurio y la cuenta
        new_user = self.user_dao.create(db, {
            "first_name": first_name,
            "last_name": last_name,
            "dni": dni,
        })

        try:
            new_account = self.account_dao.create(db, {
                "email": email,
                "password": hashed_password,
                "role": role_enum,
                "user_id": new_user.id,
            })
        except DatabaseException:
            try:
                self.user_dao.delete(db, new_user.id, soft_delete=False)
            except Exception:
                logger.error("No se pudo revertir creación de usuario %s tras fallo de cuenta", new_user.id)
            raise

        # TODO: enviar correo con credenciales (por si acaso)

        return AdminCreateUserResponse(
            user_id=new_user.id,
            account_id=new_account.id,
            email=new_account.email,
            role=new_account.role.value,
        )
