import logging
import secrets
import string

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.dao.account_dao import AccountDAO
from app.dao.user_dao import UserDAO
from app.models.account import Account
from app.models.enums.rol import Role
from app.schemas.user_schema import AdminCreateUserRequest, AdminCreateUserResponse
from app.utils.exceptions import AlreadyExistsException, UnauthorizedException, ValidationException, DatabaseException
from app.utils.security import is_email_allowed, validate_ec_dni
from app.core.config import settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

        first_name = (payload.first_name or "").strip()
        last_name = (payload.last_name or "").strip()
        email = (payload.institutional_email or "").strip().lower()
        dni = validate_ec_dni(payload.dni)
        role_normalized = (payload.role or "").strip().lower()

        if not first_name or not last_name:
            raise ValidationException("Nombre y apellidos son requeridos")

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
        temp_password = self._generate_temp_password()
        hashed_password = self._hash_password(temp_password)

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

    def _generate_temp_password(self, length: int = 14) -> str:
        """Genera contraseña temporal fuerte."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        length = max(12, min(length, 48))
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _hash_password(self, plain_password: str) -> str:
        """Hashea contraseña con bcrypt."""
        return pwd_context.hash(plain_password)
