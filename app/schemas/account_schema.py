#Esquemas Pydantic para la gestión de cuentas de usuario

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, SecretStr

from app.schemas.base_schema import BaseResponseSchema


class AccountResponse(BaseResponseSchema):
    """Respuesta de cuenta de usuario."""
    role: str
    user_id: int
    external_account_id: str


class LoginRequest(BaseModel):
    """Solicitud de inicio de sesión."""
    email: EmailStr
    password: SecretStr = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Respuesta de inicio de sesión."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    role: str


class ForgotPasswordRequest(BaseModel):
    """Solicitud para iniciar proceso de recuperación de contraseña"""
    account_id: int = Field(..., ge=1, description="Identificador local de la cuenta")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=32)
    new_password: SecretStr = Field(..., min_length=8)
    confirm_password: SecretStr = Field(..., min_length=8)

    def validate_passwords(self) -> None:
        if self.new_password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("Las contraseñas no coinciden")
