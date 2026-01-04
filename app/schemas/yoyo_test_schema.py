"""Esquemas para Yoyo Tests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateYoyoTestSchema(CreateTestBaseSchema):
    """Schema para crear un Yoyo Test (resistencia aerobia)."""

    shuttle_count: int = Field(..., gt=0, description="Número de shuttles completados")
    final_level: str = Field(..., description="Nivel final alcanzado (ej: 16.3, 18.2)")
    failures: int = Field(..., ge=0, description="Número de fallos")


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
