# app/schemas/user_schema.py
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums.rol import Role


class AdminCreateUserRequest(BaseModel):
    """Datos que el admin ingresa para crear administradores/entrenadores."""

    model_config = ConfigDict(validate_assignment=True)

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dígitos)")
    password: str = Field(..., min_length=8, max_length=64)
    role: Role = Field(..., description="Administrator o Coach")

    direction: Optional[str] = Field(default="S/N")
    phone: Optional[str] = Field(default="S/N")
    type_identification: str = Field(default="CEDULA")
    type_stament: str = Field(default="EXTERNOS")

    @field_validator("role", mode="before")
    @classmethod
    def _parse_role(cls, value: Any) -> Role:
        if isinstance(value, Role):
            if value == Role.INTERN:
                raise ValueError("Rol inválido. Use Administrator o Coach")
            return value

        if value is None:
            raise ValueError("Rol es requerido")

        raw = str(value).strip().lower()
        if raw in ("administrador", "administrator", "admin"):
            return Role.ADMINISTRATOR
        if raw in ("entrenador", "coach"):
            return Role.COACH

        raise ValueError("Rol inválido. Use Administrator o Coach")


class AdminUpdateUserRequest(AdminCreateUserRequest):
    """Datos que el admin ingresa para actualizar administradores/entrenadores."""

    pass


class AdminUpdateUserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    role: str
    updated_at: datetime
    is_active: bool


class AdminCreateUserResponse(BaseModel):
    user_id: int
    account_id: int
    full_name: str
    email: EmailStr
    role: str
    external: str


class CreatePersonInMSRequest(BaseModel):
    """Datos para crear una persona en el MS de usuarios."""

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    dni: str = Field(..., min_length=10, max_length=10)
    direction: str = Field(default="S/N")
    phone: str = Field(default="S/N")
    type_identification: str = Field(default="CEDULA")
    type_stament: str = Field(default="EXTERNOS")


class CreateLocalUserAccountRequest(BaseModel):
    """Datos para crear usuario y cuenta localmente."""

    full_name: str = Field(..., min_length=2, max_length=200)
    external: str = Field(..., min_length=30, max_length=50)
    dni: str = Field(..., min_length=10, max_length=10)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    role: Role
