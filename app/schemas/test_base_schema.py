"""Schema base para todos los tipos de tests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateTestBaseSchema(BaseModel):
    """Base para crear cualquier tipo de test."""

    date: datetime = Field(..., description="Fecha del test")
    observations: Optional[str] = None
    athlete_id: int = Field(..., description="ID del atleta que realiza el test")
    evaluation_id: int = Field(
        ..., description="ID de la evaluación a la que pertenece"
    )
