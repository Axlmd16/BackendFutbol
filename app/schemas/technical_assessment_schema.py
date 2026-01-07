"""Esquemas para Technical Assessments."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums.scale import Scale
from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class CreateTechnicalAssessmentSchema(CreateTestBaseSchema):
    """Schema para crear una Technical Assessment (evaluación técnica)."""

    ball_control: Optional[Scale] = None
    short_pass: Optional[Scale] = None
    long_pass: Optional[Scale] = None
    shooting: Optional[Scale] = None
    dribbling: Optional[Scale] = None

    @model_validator(mode="after")
    def validate_at_least_one_skill(self):
        """Validar que al menos una habilidad esté evaluada."""
        skills = [
            self.ball_control,
            self.short_pass,
            self.long_pass,
            self.shooting,
            self.dribbling,
        ]

        if all(skill is None for skill in skills):
            raise ValueError(
                "Debe evaluar al menos una habilidad técnica. "
                "Todas las habilidades están vacías."
            )
        return self


class TechnicalAssessmentResponseSchema(BaseResponseSchema):
    """Schema de respuesta para Technical Assessment."""

    test_type: str = "technical_assessment"
    date: datetime
    observations: Optional[str]
    athlete_id: int
    evaluation_id: int
    ball_control: Optional[str]
    short_pass: Optional[str]
    long_pass: Optional[str]
    shooting: Optional[str]
    dribbling: Optional[str]


class UpdateTechnicalAssessmentSchema(BaseModel):
    """Schema para actualizar una Technical Assessment."""

    date: Optional[datetime] = None
    observations: Optional[str] = None
    athlete_id: Optional[int] = Field(None, gt=0, description="ID del atleta")
    evaluation_id: Optional[int] = Field(None, gt=0, description="ID de la evaluación")
    ball_control: Optional[Scale] = None
    short_pass: Optional[Scale] = None
    long_pass: Optional[Scale] = None
    shooting: Optional[Scale] = None
    dribbling: Optional[Scale] = None


class TechnicalAssessmentFilter(BaseModel):
    """Filtros y paginación para Technical Assessments."""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    evaluation_id: Optional[int] = Field(None, gt=0)
    athlete_id: Optional[int] = Field(None, gt=0)
    search: Optional[str] = Field(None, description="Buscar por nombre de atleta")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit
