"""Esquemas para creación de usuarios administradores/entrenadores."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class AdminCreateUserRequest(BaseModel):
    """Datos que el admin ingresa para crear administradores/entrenadores."""

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dígitos)")
    password: str = Field(..., min_length=8, max_length=64)
    role: str = Field(..., description="administrator o coach")
    direction: Optional[str] = Field(default="S/N")
    phone: Optional[str] = Field(default="S/N")
    type_identification: str = Field(default="CEDULA")
    type_stament: str = Field(default="EXTERNOS")


class AdminCreateUserResponse(BaseModel):
    user_id: int
    account_id: int
    external_person_id: str   # persons.external_id
    external_account_id: str  # accounts.external_id
    full_name: str
    email: EmailStr
    role: str
