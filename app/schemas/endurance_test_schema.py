"""Esquemas para Endurance Tests."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateEnduranceTestSchema(CreateTestBaseSchema):
    """Schema para crear un Endurance Test (resistencia general)."""

    min_duration: int = Field(..., gt=0, description="Duración en minutos")
    total_distance_m: float = Field(..., gt=0, description="Distancia total en metros")


class EnduranceTestResponseSchema(BaseResponseSchema):
    """Schema de respuesta para Endurance Test."""

    date: datetime
    observations: Optional[str]
    athlete_id: int
    evaluation_id: int
    min_duration: int
    total_distance_m: float
