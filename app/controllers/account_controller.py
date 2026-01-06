from sqlalchemy.orm import Session

from app.core.config import settings
from app.dao.account_dao import AccountDAO
from app.models.account import Account
from app.schemas.account_schema import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
)
from app.utils.email_client import send_reset_email
from app.utils.exceptions import UnauthorizedException
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    hash_password,
    validate_refresh_token,
    validate_reset_token,
    verify_password,
)

# Hash ficticio para mitigar ataques de timing en login cuando el email no existe
DUMMY_PASSWORD_HASH = hash_password("DummyPass123!")


class AccountController:
    """Controlador de cuentas de usuario."""

    def __init__(self) -> None:
        self.account_dao = AccountDAO()

    def login(self, db: Session, payload: LoginRequest) -> LoginResponse:
        """Iniciar sesión y obtener un token de acceso."""
        email = payload.email.strip().lower()
        account = self.account_dao.get_by_email(db, email, only_active=True)

        if not account:
            # Verificamos contra un hash ficticio para igualar tiempos de respuesta
            verify_password(payload.password, DUMMY_PASSWORD_HASH)
            raise UnauthorizedException("Credenciales inválidas")

        if not verify_password(payload.password, account.password_hash):
            raise UnauthorizedException("Credenciales inválidas")

        access_token = self.generate_jwt(account)
        refresh_token = create_refresh_token(subject=account.id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",  # nosec
            expires_in=settings.TOKEN_EXPIRES,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRES,
        )

    def generate_jwt(self, account: Account) -> str:
        """Generar un JWT de acceso para la cuenta.

        Args:
            account: Cuenta autenticada para la que se generará el token.

        Returns:
            str: JWT firmado que incluye `sub`, rol, email y nombre.
        """
        # Obtener nombre del usuario relacionado
        full_name = account.user.full_name if account.user else None

        return create_access_token(
            subject=account.id,
            expires_seconds=settings.TOKEN_EXPIRES,
            extra_claims={
                "role": account.role.value,
                "email": account.email,
                "full_name": full_name,
            },
        )

    def request_password_reset(
        self, db: Session, payload: PasswordResetRequest
    ) -> None:  # noqa: E501
        """Genera y envía un token de restablecimiento si la cuenta existe.

        Args:
            db: Sesión de base de datos para consultar la cuenta.
            payload: Solicitud con el correo a restablecer.

        Returns:
            None. No revela si el correo existe para evitar enumeración.
        """

        email = payload.email.strip().lower()
        account = self.account_dao.get_by_email(db, email, only_active=True)

        if not account:
            return

        reset_token = create_reset_token(account.id, account.email)
        send_reset_email(
            to_email=account.email, full_name=email, reset_token=reset_token
        )

    def change_password(
        self, db: Session, user_id: int, payload: ChangePasswordRequest
    ) -> None:
        """Cambia la contraseña de un usuario autenticado.

        Args:
            db: Sesión de base de datos.
            user_id: ID del usuario autenticado.
            payload: Datos de cambio de contraseña.

        Raises:
            UnauthorizedException: Si la contraseña actual es incorrecta.
        """
        account = self.account_dao.get_by_id(db, user_id, only_active=True)
        if not account:
            raise UnauthorizedException("Cuenta no encontrada")

        if not verify_password(payload.current_password, account.password_hash):
            raise UnauthorizedException("Contraseña actual incorrecta")

        account.password_hash = hash_password(payload.new_password)
        db.commit()

    def confirm_password_reset(
        self, db: Session, payload: PasswordResetConfirm
    ) -> None:  # noqa: E501
        """Valida el token de reset y actualiza la contraseña.

        Args:
            db: Sesión de base de datos.
            payload: Token de reset y la nueva contraseña.

        Raises:
            UnauthorizedException: Si el token es inválido o la cuenta no está activa.
        """

        data = validate_reset_token(payload.token)
        account_id = int(data["sub"])

        account = self.account_dao.get_by_id(db, account_id, only_active=True)
        if not account:
            raise UnauthorizedException("Cuenta no encontrada o inactiva")

        account.password_hash = hash_password(payload.new_password)
        db.commit()

    def refresh_token(self, db: Session, payload: RefreshTokenRequest) -> LoginResponse:
        """Genera un nuevo access token usando un refresh token válido.

        Args:
            db: Sesión de base de datos.
            payload: Contiene el refresh_token a validar.

        Returns:
            LoginResponse: Nuevo access token y el mismo refresh token.

        Raises:
            UnauthorizedException: Si el refresh token es inválido o expirado.
        """
        data = validate_refresh_token(payload.refresh_token)
        account_id = int(data["sub"])

        account = self.account_dao.get_by_id(db, account_id, only_active=True)
        if not account:
            raise UnauthorizedException("Cuenta no encontrada o inactiva")

        new_access_token = self.generate_jwt(account)

        return LoginResponse(
            access_token=new_access_token,
            refresh_token=payload.refresh_token,  # Reutilizar el refresh token
            token_type="bearer",  # nosec
            expires_in=settings.TOKEN_EXPIRES,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRES,
        )
