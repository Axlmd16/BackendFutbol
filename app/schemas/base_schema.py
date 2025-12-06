"""Esquemas base compartidos para respuestas y mapeo ORM."""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class BaseSchema(BaseModel):
    """Configura conversión desde ORM y sirve como base para otros schemas."""

    model_config = ConfigDict(from_attributes=True)


class BaseResponseSchema(BaseSchema):
    """Incluye identificador, timestamps y flag de actividad para respuestas estándar."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
