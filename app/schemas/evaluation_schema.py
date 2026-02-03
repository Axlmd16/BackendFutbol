"""Esquemas para Evaluations."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.constants import (
    DATE_FORMAT_DESCRIPTION,
    TIME_FORMAT_DESCRIPTION,
    TIME_PATTERN_STRICT,
)
from app.schemas.endurance_test_schema import (
    CreateEnduranceTestSchema,
    EnduranceTestResponseSchema,
)
from app.schemas.sprint_test_schema import (
    CreateSprintTestSchema,
    SprintTestResponseSchema,
)
from app.schemas.technical_assessment_schema import (
    CreateTechnicalAssessmentSchema,
    TechnicalAssessmentResponseSchema,
)
from app.schemas.yoyo_test_schema import (
    CreateYoyoTestSchema,
    YoyoTestResponseSchema,
)

# ==========================================
# EVALUATION SCHEMAS


class CreateEvaluationSchema(BaseModel):
    """Schema para crear una nueva evaluación."""

    name: str = Field(..., description="Nombre de la evaluación")
    date: datetime = Field(..., description="Fecha y hora de la evaluación")
    time: str = Field(..., max_length=10, description="Hora en formato HH:MM")
    location: Optional[str] = Field(
        None, max_length=255, description="Ubicación de la evaluación"
    )
    observations: Optional[str] = Field(None, description="Observaciones generales")
    user_id: int = Field(..., description="ID del evaluador (usuario)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida longitud mínima y máxima del nombre."""
        if not v or len(v.strip()) < 3:
            raise ValueError(
                "El nombre de la evaluación debe tener al menos 3 caracteres"
            )
        if len(v.strip()) > 30:
            raise ValueError(
                "El nombre de la evaluación no puede exceder 30 caracteres"
            )
        return v

    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Valida formato y rango de hora HH:MM (00-23 / 00-59)."""
        if not TIME_PATTERN_STRICT.match(v or ""):
            raise ValueError(f"La hora debe estar en formato {TIME_FORMAT_DESCRIPTION}")
        hour, minute = map(int, v.split(":"))
        if hour not in range(24) or minute not in range(60):
            raise ValueError("La hora de evaluación es inválida")
        return v


class UpdateEvaluationSchema(BaseModel):
    """Schema para actualizar una evaluación existente."""

    name: Optional[str] = Field(None)
    date: Optional[datetime] = None
    time: Optional[str] = Field(
        None, max_length=10, description="Hora en formato HH:MM"
    )
    location: Optional[str] = Field(None, max_length=255)
    observations: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Valida longitud mínima y máxima del nombre si se proporciona."""
        if v is None:
            return v
        if len(v.strip()) < 3:
            raise ValueError(
                "El nombre de la evaluación debe tener al menos 3 caracteres"
            )
        if len(v.strip()) > 30:
            raise ValueError(
                "El nombre de la evaluación no puede exceder 30 caracteres"
            )
        return v

    @field_validator("time")
    @classmethod
    def validate_time(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato y rango de hora HH:MM (00-23 / 00-59) si se proporciona."""
        if v is None:
            return v
        if not TIME_PATTERN_STRICT.match(v or ""):
            raise ValueError(f"La hora debe estar en formato {TIME_FORMAT_DESCRIPTION}")
        hour, minute = map(int, v.split(":"))
        if hour not in range(24) or minute not in range(60):
            raise ValueError("La hora de evaluación es inválida")
        return v


class EvaluationResponseSchema(BaseResponseSchema):
    """Schema de respuesta para una evaluación con sus tests."""

    name: str
    date: datetime
    time: str
    location: Optional[str]
    observations: Optional[str]
    user_id: int


class EvaluationFilter(BaseModel):
    """Filtros y paginación para listar evaluaciones."""

    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(10, ge=1, le=100, description="Registros por página")
    search: Optional[str] = Field(None, description="Buscar por nombre")
    user_id: Optional[int] = Field(None, gt=0, description="Filtrar por usuario")
    date: Optional[str] = Field(
        None, description=f"Filtrar por fecha ({DATE_FORMAT_DESCRIPTION})"
    )
    location: Optional[str] = Field(None, description="Filtrar por ubicación")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


# ==========================================
# GENERIC TEST RESPONSE (para listar)


class TestResponseSchema(BaseModel):
    """Schema genérico para respuestas de tests."""

    id: int
    type: str  # "sprint_test", "yoyo_test", "endurance_test", "technical_assessment"
    date: datetime
    athlete_id: int
    evaluation_id: int
    observations: Optional[str]
    # Datos específicos según tipo
    data: dict  # Contendrá los datos específicos del tipo de test


# ==========================================
# EVALUATION WITH TESTS


class EvaluationDetailSchema(EvaluationResponseSchema):
    """Evaluación con lista detallada de tests."""

    tests: List[TestResponseSchema] = []


__all__ = [
    "CreateEvaluationSchema",
    "UpdateEvaluationSchema",
    "EvaluationResponseSchema",
    "EvaluationDetailSchema",
    "TestResponseSchema",
    # Importados desde módulos específicos
    "CreateSprintTestSchema",
    "SprintTestResponseSchema",
    "CreateYoyoTestSchema",
    "YoyoTestResponseSchema",
    "CreateEnduranceTestSchema",
    "EnduranceTestResponseSchema",
    "CreateTechnicalAssessmentSchema",
    "TechnicalAssessmentResponseSchema",
]
