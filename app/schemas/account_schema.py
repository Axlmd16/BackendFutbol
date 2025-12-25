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