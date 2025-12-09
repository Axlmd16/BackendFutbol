"""Esquemas Pydantic para operaciones sobre evaluadores."""

from typing import Optional

from pydantic import Field

from app.schemas.base_schema import BaseResponseSchema, BaseSchema


# Esquemas específicos para evaluadores 
class EvaluatorBase(BaseSchema):
    """Campos compartidos para crear o actualizar evaluadores."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    dni: str = Field(..., min_length=5, max_length=20)


# Esquemas para crear, actualizar y responder con evaluadores
class EvaluatorCreate(EvaluatorBase):
    """Payload de creación."""

    pass


# Esquema para actualizar evaluadores
class EvaluatorUpdate(BaseSchema):
    """Campos opcionales para actualizar un evaluador."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    dni: Optional[str] = Field(None, min_length=5, max_length=20)


# Esquema de respuesta con metadatos base
class EvaluatorResponse(BaseResponseSchema):
    """Respuesta estándar con metadatos base."""

    first_name: str
    last_name: str
    dni: str
