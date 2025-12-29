"""Esquemas para Evaluations y Tests."""

import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.base_schema import BaseResponseSchema

# ==========================================
# EVALUATION SCHEMAS


class CreateEvaluationSchema(BaseModel):
    """Schema para crear una nueva evaluación."""

    name: str = Field(
        ..., min_length=3, max_length=100, description="Nombre de la evaluación"
    )
    date: datetime = Field(..., description="Fecha y hora de la evaluación")
    time: str = Field(..., max_length=10, description="Hora en formato HH:MM")
    location: Optional[str] = Field(
        None, max_length=255, description="Ubicación de la evaluación"
    )
    observations: Optional[str] = Field(None, description="Observaciones generales")
    user_id: int = Field(..., description="ID del evaluador (usuario)")


class UpdateEvaluationSchema(BaseModel):
    """Schema para actualizar una evaluación existente."""

    name: Optional[str] = Field(None, min_length=3, max_length=100)
    date: Optional[datetime] = None
    time: Optional[str] = Field(None, max_length=10)
    location: Optional[str] = Field(None, max_length=255)
    observations: Optional[str] = None


class EvaluationResponseSchema(BaseResponseSchema):
    """Schema de respuesta para una evaluación con sus tests."""

    name: str
    date: datetime
    time: str
    location: Optional[str]
    observations: Optional[str]
    user_id: int


# ==========================================
# TEST SCHEMAS (Base)


class CreateTestBaseSchema(BaseModel):
    """Base para crear cualquier tipo de test."""

    date: datetime = Field(..., description="Fecha del test")
    observations: Optional[str] = None
    athlete_id: int = Field(..., description="ID del atleta que realiza el test")
    evaluation_id: int = Field(
        ..., description="ID de la evaluación a la que pertenece"
    )


# ==========================================
# SPRINT TEST SCHEMAS


class CreateSprintTestSchema(CreateTestBaseSchema):
    """Schema para crear un Sprint Test (velocidad)."""

    distance_meters: float = Field(..., gt=0, description="Distancia en metros")
    time_0_10_s: float = Field(..., gt=0, description="Tiempo 0-10 metros")
    time_0_30_s: float = Field(..., gt=0, description="Tiempo 0-30 metros")


class SprintTestResponseSchema(BaseResponseSchema):
    """Schema de respuesta para Sprint Test."""

    date: datetime
    observations: Optional[str]
    athlete_id: int
    evaluation_id: int
    distance_meters: float
    time_0_10_s: float
    time_0_30_s: float


# ==========================================
# YOYO TEST SCHEMAS


class CreateYoyoTestSchema(CreateTestBaseSchema):
    """Schema para crear un Yoyo Test (resistencia aerobia)."""

    shuttle_count: int = Field(..., gt=0, description="Número de shuttles completados")
    final_level: str = Field(..., description="Nivel final alcanzado (ej: 16.3, 18.2)")
    failures: int = Field(..., ge=0, description="Número de fallos")


class YoyoTestResponseSchema(BaseResponseSchema):
    """Schema de respuesta para Yoyo Test."""

    date: datetime
    observations: Optional[str]
    athlete_id: int
    evaluation_id: int
    shuttle_count: int
    final_level: str
    failures: int


# ==========================================
# ENDURANCE TEST SCHEMAS


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


# ==========================================
# TECHNICAL ASSESSMENT SCHEMAS


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
