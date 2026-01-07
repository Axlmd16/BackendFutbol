"""Schema base para todos los tipos de tests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CreateTestBaseSchema(BaseModel):
    """Base para crear cualquier tipo de test."""

    date: datetime = Field(..., description="Fecha del test")
    observations: Optional[str] = None
    athlete_id: int = Field(..., description="ID del atleta que realiza el test")
    evaluation_id: int = Field(
        ..., description="ID de la evaluación a la que pertenece"
    )

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, v: datetime) -> datetime:
        """Validar que la fecha del test no sea futura."""
        if v > datetime.now():
            raise ValueError(
                "La fecha del test no puede ser futura. "
                f"Fecha ingresada: {v.strftime('%Y-%m-%d %H:%M')}"
            )
        return v
