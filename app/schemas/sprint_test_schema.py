"""Esquemas para Sprint Tests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateSprintTestSchema(CreateTestBaseSchema):
    """Schema para crear un Sprint Test (velocidad)."""

    distance_meters: float = Field(..., description="Distancia en metros (máx 1000m)")
    time_0_10_s: float = Field(..., description="Tiempo 0-10 metros (máx 60s)")
    time_0_30_s: float = Field(..., description="Tiempo 0-30 metros (máx 60s)")

    @field_validator("distance_meters")
    @classmethod
    def validate_distance(cls, v: float) -> float:
        """Validar distancia en rango válido."""
        if v <= 0:
            raise ValueError("La distancia debe ser mayor a 0 metros")
        if v > 1000:
            raise ValueError("La distancia debe ser menor o igual a 1000 metros")
        return v

    @field_validator("time_0_10_s", "time_0_30_s")
    @classmethod
    def validate_time(cls, v: float) -> float:
        """Validar tiempo en rango válido."""
        if v <= 0:
            raise ValueError("El tiempo debe ser mayor a 0 segundos")
        if v > 60:
            raise ValueError("El tiempo debe ser menor o igual a 60 segundos")
        return v

    @model_validator(mode="after")
    def validate_sprint_times(self):
        """Validar lógica física de tiempos de sprint."""
        if self.time_0_10_s >= self.time_0_30_s:
            raise ValueError(
                f"El tiempo 0-10m ({self.time_0_10_s}s) debe ser menor que "
                f"el tiempo 0-30m ({self.time_0_30_s}s). "
                "Revise los valores ingresados."
            )
        return self


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
