"""Esquemas para Sprint Tests."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateSprintTestSchema(CreateTestBaseSchema):
    """Schema para crear un Sprint Test (velocidad)."""

    distance_meters: float = Field(..., gt=0, description="Distancia en metros")
    time_0_10_s: float = Field(..., gt=0, description="Tiempo 0-10 metros")
    time_0_30_s: float = Field(..., gt=0, description="Tiempo 0-30 metros")


class SprintTestResponseSchema(BaseResponseSchema):
    """Schema de respuesta para Sprint Test."""

    test_type: str = "sprint_test"
    date: datetime
    observations: Optional[str]
    athlete_id: int
    evaluation_id: int
    distance_meters: float
    time_0_10_s: float
    time_0_30_s: float
