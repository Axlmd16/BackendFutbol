"""Esquemas Pydantic para inscripcion de deportistas UNL."""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.base_schema import BaseSchema


class AthleteInscriptionDTO(BaseModel):
    """Datos para alta de deportista UNL."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: str
    last_name: str
    dni: str
    phone: Optional[str] = None
    birth_date: Optional[str] = None  # YYYY-MM-DD
    weight: Optional[float] = None
    height: Optional[float] = None


class AthleteInscriptionResponseDTO(BaseSchema):
    """Respuesta al registrar un deportista UNL."""

    athlete_id: int
    statistic_id: int
    full_name: str
    dni: str
