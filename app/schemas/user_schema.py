"""Esquemas Pydantic para operaciones de usuario."""

from pydantic import BaseModel, EmailStr, Field

class AdminCreateUserRequest(BaseModel):
    """Payload requerido para que un admin cree otro usuario."""

    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    correo_institucional: EmailStr = Field(..., description="Correo corporativo del usuario")
    dni: str = Field(..., min_length=6, max_length=15, description="Documento de identidad sin caracteres especiales")
    rol: str = Field(..., description="administrador o entrenador")

class AdminCreateUserResponse(BaseModel):
    """Datos mínimos de usuario y cuenta creados."""

    user_id: int
    account_id: int
    email: EmailStr
    role: str
