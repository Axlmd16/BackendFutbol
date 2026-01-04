"""Esquemas para Sprint Tests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateSprintTestSchema(CreateTestBaseSchema):
    """Schema para crear un Sprint Test (velocidad)."""

    distance_meters: float = Field(..., gt=0, description="Distancia en metros")
    time_0_10_s: float = Field(..., gt=0, description="Tiempo 0-10 metros")
    time_0_30_s: float = Field(..., gt=0, description="Tiempo 0-30 metros")


class UpdateSprintTestSchema(BaseModel):
    """Schema para actualizar un Sprint Test."""

    date: Optional[datetime] = None
    observations: Optional[str] = None
    athlete_id: Optional[int] = Field(None, gt=0, description="ID del atleta")
    evaluation_id: Optional[int] = Field(None, gt=0, description="ID de la evaluación")
    distance_meters: Optional[float] = Field(
        None, gt=0, description="Distancia en metros"
    )
    time_0_10_s: Optional[float] = Field(None, gt=0, description="Tiempo 0-10 metros")
    time_0_30_s: Optional[float] = Field(None, gt=0, description="Tiempo 0-30 metros")


class SprintTestFilter(BaseModel):
    """Filtros y paginación para Sprint Tests."""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    evaluation_id: Optional[int] = Field(None, gt=0)
    athlete_id: Optional[int] = Field(None, gt=0)
    search: Optional[str] = Field(None, description="Buscar por nombre de atleta")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


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

    # Campos calculados
    time_10_30_s: Optional[float] = Field(
        None, description="Tiempo del segmento 10-30 metros (calculado)"
    )
    avg_speed_ms: Optional[float] = Field(
        None, description="Velocidad promedio en m/s (calculada)"
    )
    estimated_max_speed: Optional[float] = Field(
        None, description="Velocidad máxima estimada en m/s (calculada)"
    )

    model_config = {"from_attributes": True}
