#Esquemas Pydantic para la gestión de cuentas de usuario

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, SecretStr

from app.schemas.base_schema import BaseResponseSchema

#Campos comunes para crear o actualizar cuentas
class AccountBase(BaseModel):
    email: EmailStr = Field(..., description="Correo institucional del usuario")
    role: str = Field(..., description="Rol asignado")

#Esquema para crear cuentas con contraseña requerida
class AccountCreate(AccountBase):
    password: str = Field(..., min_length=8)


#Esquema para actualizar cuentas con campos opcionales
class AccountUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


#Esquema de respuesta para exponer cuentas
class AccountResponse(BaseResponseSchema):
    email: EmailStr
    role: str
    user_id: int

#Credenciales de inicio de sesión
class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(..., min_length=8)



#Respuesta de inicio de sesión con tokens y rol
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    role: str

#Solicitud para iniciar proceso de recuperación de contraseña
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


#Solicitud para restablecer contraseña
class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=32)
    new_password: SecretStr = Field(..., min_length=8)
    confirm_password: SecretStr = Field(..., min_length=8)

    def validate_passwords(self) -> None:
        if self.new_password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("Las contraseñas no coinciden")
