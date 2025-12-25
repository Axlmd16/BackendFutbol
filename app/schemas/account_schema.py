from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Datos solicitados para iniciar sesión."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)

class LoginResponse(BaseModel):
    """Datos respuesta al iniciar sesión."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordResetRequest(BaseModel):
    """Datos para solicitar restablecimiento de contraseña."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Datos para confirmar restablecimiento de contraseña."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=64)