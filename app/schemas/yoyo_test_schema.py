"""Esquemas para Yoyo Tests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateYoyoTestSchema(CreateTestBaseSchema):
    """Schema para crear un Yoyo Test (resistencia aerobia)."""

    shuttle_count: int = Field(..., description="Número de shuttles completados (máx 1000)")
    final_level: str = Field(..., description="Nivel final alcanzado (ej: 16.3, 18.2)")
    failures: int = Field(..., description="Número de fallos")

    @field_validator("shuttle_count")
    @classmethod
    def validate_shuttle_count(cls, v: int) -> int:
        """Validar número de shuttles en rango válido."""
        if v <= 0:
            raise ValueError("El número de shuttles debe ser mayor a 0")
        if v > 1000:
            raise ValueError("El número de shuttles debe ser menor o igual a 1000")
        return v

    @field_validator("failures")
    @classmethod
    def validate_failures(cls, v: int) -> int:
        """Validar número de fallos no negativo."""
        if v < 0:
            raise ValueError("El número de fallos no puede ser negativo")
        return v

    @field_validator("final_level")
    @classmethod
    def validate_final_level_format(cls, v: str) -> str:
        """Validar formato estricto XX.Y del nivel final."""
        import re

        pattern = r"^\d{1,2}\.\d{1}$"
        if not re.match(pattern, v):
            raise ValueError(
                f"El nivel final debe tener el formato XX.Y (ej: 16.3, 18.2). "
                f"Valor ingresado: '{v}'"
            )
        return v


class UpdateYoyoTestSchema(BaseModel):
    """Schema para actualizar un Yoyo Test."""

    date: Optional[datetime] = None
    observations: Optional[str] = None
    athlete_id: Optional[int] = Field(None, gt=0, description="ID del atleta")
    evaluation_id: Optional[int] = Field(None, gt=0, description="ID de la evaluación")
    shuttle_count: Optional[int] = Field(
        None, gt=0, description="Número de shuttles completados"
    )
    final_level: Optional[str] = Field(
        None, description="Nivel final alcanzado (ej: 16.3, 18.2)"
    )
    failures: Optional[int] = Field(None, ge=0, description="Número de fallos")


class YoyoTestFilter(BaseModel):
    """Filtros y paginación para Yoyo Tests."""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    evaluation_id: Optional[int] = Field(None, gt=0)
    athlete_id: Optional[int] = Field(None, gt=0)
    search: Optional[str] = Field(None, description="Buscar por nombre de atleta")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


class YoyoTestResponseSchema(BaseResponseSchema):
    """Schema de respuesta para Yoyo Test."""

    test_type: str = "yoyo_test"
    date: datetime
    observations: Optional[str]
    athlete_id: int
    evaluation_id: int
    shuttle_count: int
    final_level: str
    failures: int

    # Campos calculados
    total_distance: Optional[float] = Field(
        None, description="Distancia total recorrida en metros (calculada)"
    )
    vo2_max: Optional[float] = Field(
        None, description="VO2 máximo estimado en ml/kg/min (calculado)"
    )

    model_config = {"from_attributes": True}
