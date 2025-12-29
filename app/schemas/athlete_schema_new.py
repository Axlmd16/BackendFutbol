"""Esquemas Pydantic para inscripcion de deportistas UNL."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

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
    type_stament: Optional[str] = None  # DOCENTES, ADMINISTRATIVOS, ESTUDIANTES, EXTERNOS
    
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


# Schemas para gestión de atletas (HU-009)

class AthleteResponse(BaseSchema):
    """Respuesta con datos básicos del atleta para listados."""

    id: int
    full_name: str
    dni: str
    type_athlete: str
    sex: str
    is_active: bool


class AthleteDetailResponse(BaseSchema):
    """Respuesta con detalles completos del atleta incluyendo información del MS."""

    id: int
    external_person_id: str
    full_name: str
    dni: str
    type_athlete: str
    date_of_birth: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    sex: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    ms_person_data: Optional[dict] = Field(
        default=None, description="Información de la persona desde el MS de usuarios"
    )


class AthleteUpdateDTO(BaseModel):
    """Datos para actualizar un atleta (solo campos editables)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    height: Optional[float] = Field(default=None, ge=0)
    weight: Optional[float] = Field(default=None, ge=0)
    direction: Optional[str] = Field(default=None, description="Dirección")
    phone: Optional[str] = Field(default=None, description="Teléfono")


class AthleteFilter(BaseModel):
    """Filtros para búsqueda y paginación de atletas."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    search: Optional[str] = Field(None, description="Búsqueda por nombre o DNI")
    type_athlete: Optional[str] = Field(None, description="UNL, EXTERNO")
    sex: Optional[str] = Field(None, description="MALE, FEMALE, OTHER")
    is_active: Optional[bool] = Field(None, description="Estado activo/inactivo")
    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(10, ge=1, le=100, description="Registros por página")

    @property
    def skip(self) -> int:
        """Calcula automáticamente el offset para la BD."""
        return (self.page - 1) * self.limit
