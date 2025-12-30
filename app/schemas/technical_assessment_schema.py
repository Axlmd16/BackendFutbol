"""Esquemas para Technical Assessments."""

from datetime import datetime
from typing import Optional

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema
from app.models.enums.scale import Scale


class CreateTechnicalAssessmentSchema(CreateTestBaseSchema):
    """Schema para crear una Technical Assessment (evaluación técnica)."""

    ball_control: Optional[Scale] = None
    short_pass: Optional[Scale] = None
    long_pass: Optional[Scale] = None
    shooting: Optional[Scale] = None
    dribbling: Optional[Scale] = None


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
