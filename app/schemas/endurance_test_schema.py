"""Esquemas para Endurance Tests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateEnduranceTestSchema(CreateTestBaseSchema):
    """Schema para crear un Endurance Test (resistencia general)."""

    min_duration: int = Field(..., description="Duración en minutos")
    total_distance_m: float = Field(..., description="Distancia total en metros")

    @field_validator("min_duration")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Validar duración en rango realista."""
        if v <= 0:
            raise ValueError("La duración debe ser mayor a 0 minutos")
        if v > 180:
            raise ValueError("La duración debe ser menor o igual a 180 minutos (3 horas)")
        return v

    @field_validator("total_distance_m")
    @classmethod
    def validate_distance(cls, v: float) -> float:
        """Validar distancia en rango realista."""
        if v <= 0:
            raise ValueError("La distancia debe ser mayor a 0 metros")
        if v > 50000:
            raise ValueError("La distancia debe ser menor o igual a 50000 metros (50 km)")
        return v

    @model_validator(mode="after")
    def validate_pace_realistic(self):
        """Validar que el ritmo sea físicamente posible (no más de 800m/min)."""
        pace_m_per_min = self.total_distance_m / self.min_duration
        
        # Ritmo máximo humano sostenido: ~800 m/min (récord mundial de maratón ~350 m/min)
        if pace_m_per_min > 800:
            raise ValueError(
                f"El ritmo calculado ({pace_m_per_min:.1f} m/min) es físicamente imposible. "
                f"Verifique que la distancia ({self.total_distance_m:.0f}m) y duración "
                f"({self.min_duration} min) sean correctas."
            )
        
        # Ritmo mínimo razonable: ~50 m/min (caminata muy lenta)
        if pace_m_per_min < 50:
            raise ValueError(
                f"El ritmo calculado ({pace_m_per_min:.1f} m/min) es demasiado lento. "
                f"Verifique que la distancia ({self.total_distance_m:.0f}m) y duración "
                f"({self.min_duration} min) sean correctas."
            )
        
        return self


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
    search: Optional[str] = Field(None, description="Buscar por nombre de atleta")

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
