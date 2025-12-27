from fastapi import APIRouter

from app.controllers.technical_assessment_controller import (
    TechnicalAssessmentController,
)

router = APIRouter(prefix="/technical-assessments", tags=["TechnicalAssessments"])
technical_assessment_controller = TechnicalAssessmentController()
