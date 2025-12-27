"""Esquemas Pydantic para inscripcion de deportistas UNL."""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.base_schema import BaseSchema


class AthleteInscriptionDTO(BaseModel):
    """Datos para alta de deportista UNL."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    # Datos básicos de la persona
    first_name: str
    last_name: str
    dni: str
    phone: Optional[str] = None
    direction: Optional[str] = None
    type_identification: Optional[str] = None  # CEDULA, PASAPORTE, RUC
    type_stament: Optional[str] = None  # DOCENTES, ADMINISTRATIVOS, etc.
    
    # Datos específicos del atleta
    birth_date: Optional[str] = None  # YYYY-MM-DD
    sex: Optional[str] = None  # MALE, FEMALE
    type_athlete: Optional[str] = None  # UNL, EXTERNO
    weight: Optional[float] = None
    height: Optional[float] = None


class AthleteInscriptionResponseDTO(BaseSchema):
    """Respuesta al registrar un deportista UNL."""

    athlete_id: int
    statistic_id: int
    full_name: str
    dni: str
