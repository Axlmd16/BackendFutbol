"""Esquemas para Endurance Tests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateEnduranceTestSchema(CreateTestBaseSchema):
    """Schema para crear un Endurance Test (resistencia general)."""

    min_duration: int = Field(..., gt=0, description="Duración en minutos")
    total_distance_m: float = Field(..., gt=0, description="Distancia total en metros")


class UpdateEnduranceTestSchema(BaseModel):
    """Schema para actualizar un Endurance Test."""

    date: Optional[datetime] = None
    observations: Optional[str] = None
    athlete_id: Optional[int] = Field(None, gt=0, description="ID del atleta")
    evaluation_id: Optional[int] = Field(None, gt=0, description="ID de la evaluación")
    min_duration: Optional[int] = Field(None, gt=0, description="Duración en minutos")
    total_distance_m: Optional[float] = Field(
        None, gt=0, description="Distancia total en metros"
    )


class EnduranceTestFilter(BaseModel):
    """Filtros y paginación para Endurance Tests."""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    evaluation_id: Optional[int] = Field(None, gt=0)
    athlete_id: Optional[int] = Field(None, gt=0)

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


class EnduranceTestResponseSchema(BaseResponseSchema):
    """Schema de respuesta para Endurance Test."""

    test_type: str = "endurance_test"
    date: datetime
    observations: Optional[str]
    athlete_id: int
    evaluation_id: int
    min_duration: int
    total_distance_m: float

    # Campos calculados
    pace_min_per_km: Optional[float] = Field(
        None, description="Ritmo en minutos por kilómetro (calculado)"
    )
    estimated_vo2max: Optional[float] = Field(
        None, description="VO2 máximo estimado en ml/kg/min (calculado)"
    )

    model_config = {"from_attributes": True}
