"""Esquemas para Technical Assessments."""

import enum
from datetime import datetime
from typing import Optional

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


class ScaleEnum(str, enum.Enum):
    """Escala de valoración técnica."""

    VERY_LOW = "MUY_BAJO"
    LOW = "BAJO"
    MEDIUM = "MEDIO"
    HIGH = "ALTO"
    VERY_HIGH = "MUY_ALTO"


class CreateTechnicalAssessmentSchema(CreateTestBaseSchema):
    """Schema para crear una Technical Assessment (evaluación técnica)."""

    ball_control: Optional[ScaleEnum] = None
    short_pass: Optional[ScaleEnum] = None
    long_pass: Optional[ScaleEnum] = None
    shooting: Optional[ScaleEnum] = None
    dribbling: Optional[ScaleEnum] = None


class TechnicalAssessmentResponseSchema(BaseResponseSchema):
    """Schema de respuesta para Technical Assessment."""

    date: datetime
    observations: Optional[str]
    athlete_id: int
    evaluation_id: int
    ball_control: Optional[str]
    short_pass: Optional[str]
    long_pass: Optional[str]
    shooting: Optional[str]
    dribbling: Optional[str]
