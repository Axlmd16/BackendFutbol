"""Esquemas para Yoyo Tests."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base_schema import BaseResponseSchema
from app.schemas.test_base_schema import CreateTestBaseSchema


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
