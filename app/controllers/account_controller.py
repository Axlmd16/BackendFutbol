from sqlalchemy.orm import Session

from app.core.config import settings
from app.dao.account_dao import AccountDAO
from app.schemas.account_schema import (
    LoginRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.utils.exceptions import NotFoundException, UnauthorizedException
from app.utils.security import (
    create_access_token,
    create_reset_token,
    hash_password,
    validate_reset_token,
    verify_password,
)


class AccountController:
    """Controlador de cuentas de usuario."""

    def __init__(self) -> None:
        self.account_dao = AccountDAO()

    def login(self, db: Session, payload: LoginRequest) -> LoginResponse:
        """Iniciar sesión y obtener un token de acceso."""
        email = payload.email.strip().lower()
        account = self.account_dao.get_by_email(db, email, only_active=True)

        if not account:
            raise UnauthorizedException("Credenciales inválidas")

        if not verify_password(payload.password, account.password_hash):
            raise UnauthorizedException("Credenciales inválidas")

        token = self.generate_jwt(account)

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.TOKEN_EXPIRES,
        )


    def generate_jwt(self, account) -> str:
        """Generar un JWT para una cuenta dada."""
        return create_access_token(
            subject=account.id,
            expires_seconds=settings.TOKEN_EXPIRES,
            extra_claims={"role": account.role.value, "email": account.email},
        ) 

    def request_password_reset(self, db: Session, payload: PasswordResetRequest) -> str:
        """Genera un token de reset."""

        email = payload.email.strip().lower()
        account = self.account_dao.get_by_email(db, email, only_active=True)

        if not account:
            raise NotFoundException("Cuenta no encontrada")

        return create_reset_token(account.id, account.email)

    def confirm_password_reset(self, db: Session, payload: PasswordResetConfirm) -> None:
        """Valida el token de reset y actualiza la contraseña."""

        data = validate_reset_token(payload.token)
        account_id = int(data["sub"])

        account = self.account_dao.get_by_id(db, account_id, only_active=True)
        if not account:
            raise UnauthorizedException("Token inválido o cuenta inactiva")

        account.password_hash = hash_password(payload.new_password)
        db.commit()
