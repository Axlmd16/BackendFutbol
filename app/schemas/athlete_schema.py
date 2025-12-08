"""Esquemas para validación y serialización de datos de deportistas."""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.schemas.base_schema import BaseResponseSchema
import re


class AthleteInscriptionDTO(BaseModel):
    """
    DTO de entrada para inscripción de deportista de la comunidad UNL.
    
    Contiene validaciones para datos personales, institucionales y físicos
    según las reglas de negocio de la institución.
    """
    
    # Datos personales
    first_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre del deportista"
    )
    last_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Apellido del deportista"
    )
    dni: str = Field(
        ...,
        min_length=5,
        max_length=20,
        description="DNI del deportista"
    )
    phone: str = Field(
        ...,
        min_length=7,
        max_length=20,
        description="Número de teléfono"
    )
    birth_date: str = Field(
        ...,
        description="Fecha de nacimiento (YYYY-MM-DD)"
    )
    
    # Datos institucionales
    institutional_email: EmailStr = Field(
        ..., 
        description="Email institucional de la UNL (@unl.edu.ar o similar)"
    )
    university_role: str = Field(
        ..., 
        description="Rol en la institución: STUDENT, TEACHER, ADMIN, WORKER"
    )
    
    # Datos físicos
    weight: str = Field(
        ..., 
        description="Peso en kilogramos"
    )
    height: str = Field(
        ..., 
        description="Altura en centímetros"
    )
    
    @field_validator("birth_date")
    @classmethod
    def validate_birth_date_format(cls, v: str) -> str:
        """Valida formato de fecha (YYYY-MM-DD)."""
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, v):
            raise ValueError("birth_date debe estar en formato YYYY-MM-DD")
        return v
    
    @field_validator("university_role")
    @classmethod
    def validate_university_role(cls, v: str) -> str:
        """Valida que el rol universitario sea uno de los permitidos."""
        valid_roles = {"STUDENT", "TEACHER", "ADMIN", "WORKER"}
        v_upper = v.upper()
        if v_upper not in valid_roles:
            raise ValueError(f"university_role debe ser uno de: {', '.join(valid_roles)}")
        return v_upper
    
    @field_validator("first_name", "last_name")
    @classmethod
    def sanitize_text_fields(cls, v: str) -> str:
        """
        Sanitiza campos de texto para prevenir XSS/SQLi.
        Elimina caracteres especiales peligrosos.
        """
        # Permitir solo letras, espacios, guiones y apóstrofos
        if not re.match(r"^[a-zA-Z\s\-'áéíóúñüÁÉÍÓÚÑÜ]+$", v):
            raise ValueError("El campo contiene caracteres no permitidos")
        return v.strip()
    
    @field_validator("weight", "height")
    @classmethod
    def validate_numeric_fields(cls, v: str) -> str:
        """Valida que peso y altura sean valores numéricos válidos."""
        try:
            float_val = float(v)
            if float_val <= 0:
                raise ValueError("El valor debe ser positivo")
        except ValueError:
            raise ValueError("El campo debe contener un valor numérico válido")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "12345678",
                "phone": "3424123456",
                "birth_date": "1998-05-15",
                "institutional_email": "juan.perez@unl.edu.ar",
                "university_role": "STUDENT",
                "weight": "75.5",
                "height": "180"
            }
        }
    }


class AthleteResponseDTO(BaseResponseSchema):
    """
    DTO de respuesta para retornar datos del deportista creado.
    Incluye información básica sin datos sensibles.
    """
    first_name: str
    last_name: str
    dni: str
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    institutional_email: Optional[str] = None
    university_role: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None
    type_athlete: str


class AthleteInscriptionResponseDTO(BaseModel):
    """Respuesta completa de inscripción con datos del deportista e ID de estadísticas."""
    
    athlete_id: int = Field(..., description="ID del deportista creado")
    statistic_id: int = Field(..., description="ID del registro de estadísticas")
    first_name: str
    last_name: str
    institutional_email: str
    message: str = Field(default="Deportista registrado exitosamente")
