"""Esquemas de validación para deportistas y representantes legales."""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from datetime import date
from app.schemas.base_schema import BaseResponseSchema
import re


class RepresentativeCreateSchema(BaseModel):
    """
    Schema para crear un representante legal.
    
    Valida los datos del tutor o padre/madre que autoriza
    la participación del menor en la escuela de fútbol.
    """
    
    first_name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="Nombres del representante legal"
    )
    last_name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="Apellidos del representante legal"
    )
    dni: str = Field(
        ..., 
        min_length=8, 
        max_length=20,
        description="Documento de identidad del representante"
    )
    address: str = Field(
        ..., 
        min_length=5, 
        max_length=255,
        description="Dirección de domicilio completa"
    )
    phone: str = Field(
        ..., 
        min_length=7, 
        max_length=20,
        description="Número de teléfono de contacto"
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico válido"
    )
    
    @field_validator('dni')
    @classmethod
    def validate_dni(cls, value: str) -> str:
        """
        Valida y sanitiza el DNI para prevenir inyección.
        Solo permite caracteres alfanuméricos y guiones.
        """
        if not re.match(r'^[A-Za-z0-9-]+$', value):
            raise ValueError('El DNI solo puede contener letras, números y guiones')
        return value.strip().upper()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """
        Valida y sanitiza el teléfono.
        Solo permite números, espacios, guiones y paréntesis.
        """
        if not re.match(r'^[0-9\s\-\(\)\+]+$', value):
            raise ValueError('El teléfono contiene caracteres no válidos')
        return value.strip()
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, value: str) -> str:
        """
        Valida y sanitiza nombres para prevenir inyección.
        Solo permite letras, espacios y caracteres latinos.
        """
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', value):
            raise ValueError('Los nombres solo pueden contener letras y espacios')
        return value.strip().title()


class RepresentativeResponseSchema(BaseResponseSchema):
    """Schema de respuesta para representante legal."""
    
    first_name: str
    last_name: str
    dni: str
    address: str
    phone: str
    email: str


class MinorAthleteCreateSchema(BaseModel):
    """
    Schema para crear un deportista menor de edad.
    
    Incluye validaciones específicas para menores y datos
    del representante legal responsable.
    """
    
    # Datos del deportista menor
    first_name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="Nombres del deportista menor"
    )
    last_name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="Apellidos del deportista menor"
    )
    dni: str = Field(
        ..., 
        min_length=8, 
        max_length=20,
        description="Documento de identidad del menor"
    )
    birth_date: date = Field(
        ...,
        description="Fecha de nacimiento del menor (debe ser < 18 años)"
    )
    sex: str = Field(
        ...,
        pattern="^(M|F)$",
        description="Sexo del deportista (M o F)"
    )
    
    # Datos del representante legal
    representative: RepresentativeCreateSchema = Field(
        ...,
        description="Información completa del representante legal"
    )
    
    # Autorización parental
    parental_authorization: bool = Field(
        ...,
        description="Autorización expresa de los padres/tutores (debe ser True)"
    )
    
    @field_validator('dni')
    @classmethod
    def validate_dni(cls, value: str) -> str:
        """
        Valida y sanitiza el DNI del menor para prevenir inyección.
        Solo permite caracteres alfanuméricos y guiones.
        """
        if not re.match(r'^[A-Za-z0-9-]+$', value):
            raise ValueError('El DNI solo puede contener letras, números y guiones')
        return value.strip().upper()
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, value: str) -> str:
        """
        Valida y sanitiza nombres para prevenir inyección.
        Solo permite letras, espacios y caracteres latinos.
        """
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', value):
            raise ValueError('Los nombres solo pueden contener letras y espacios')
        return value.strip().title()
    
    @field_validator('birth_date')
    @classmethod
    def validate_minor_age(cls, value: date) -> date:
        """
        Valida que el deportista sea efectivamente menor de edad.
        Calcula la edad basándose en la fecha de nacimiento.
        """
        from datetime import date as date_type
        today = date_type.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age >= 18:
            raise ValueError('El deportista debe ser menor de 18 años para usar este registro')
        
        if age < 5:
            raise ValueError('El deportista debe tener al menos 5 años')
        
        return value
    
    @field_validator('parental_authorization')
    @classmethod
    def validate_authorization(cls, value: bool) -> bool:
        """
        Valida que exista autorización parental expresa.
        Este es un requisito legal obligatorio para menores.
        """
        if not value:
            raise ValueError('Se requiere autorización parental explícita para registrar menores de edad')
        return value


class AthleteResponseSchema(BaseResponseSchema):
    """Schema de respuesta para deportista."""
    
    first_name: str
    last_name: str
    dni: str
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    type_athlete: str
    representative_id: Optional[int] = None
    parental_authorization: Optional[str] = None


class MinorAthleteResponseSchema(BaseModel):
    """
    Schema de respuesta completa para registro de menor de edad.
    Incluye datos del atleta y del representante legal.
    """
    
    athlete: AthleteResponseSchema
    representative: RepresentativeResponseSchema
