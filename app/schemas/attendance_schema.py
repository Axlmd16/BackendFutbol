"""Esquemas Pydantic para asistencias (creación/consulta/respuesta)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.base_schema import BaseSchema


class AttendanceItemCreate(BaseModel):
    """Registro de asistencia individual para un atleta."""

    athlete_id: int = Field(..., description="ID del atleta")
    is_present: bool = Field(default=True, description="¿Está presente?")
    justification: str | None = Field(
        default=None, max_length=500, description="Justificación si está ausente"
    )

    @field_validator("justification", mode="before")
    @classmethod
    def clean_justification(cls, value):
        """Si está presente, la justificación debe ser None."""
        if value is not None and isinstance(value, str):
            value = value.strip()
            return value if value else None
        return value


class AttendanceBulkCreate(BaseModel):
    """Schema para crear múltiples registros de asistencia."""

    model_config = ConfigDict(str_strip_whitespace=True)

    attendance_date: date = Field(
        ..., alias="date", description="Fecha de la asistencia (YYYY-MM-DD)"
    )
    time: str | None = Field(
        default=None,
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Hora de la asistencia (HH:MM). "
        "Si no se envía, se usa la hora actual.",
    )
    records: list[AttendanceItemCreate]


class AttendanceResponse(BaseSchema):
    """Respuesta de un registro de asistencia."""

    id: int
    date: datetime
    time: str
    is_present: bool
    justification: str | None = None
    athlete_id: int
    athlete_name: str | None = None
    athlete_dni: str | None = None
    athlete_type: str | None = None
    user_dni: str
    created_at: datetime
    is_active: bool


class AttendanceFilter(BaseModel):
    """Filtros para consultar asistencias."""

    attendance_date: date = Field(
        ..., alias="date", description="Fecha de la asistencia (YYYY-MM-DD)"
    )
    type_athlete: str | None = Field(
        default=None, description="Tipo de atleta para filtrar"
    )
    search: str | None = Field(default=None, description="Búsqueda por nombre o DNI")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)

    @property
    def skip(self) -> int:
        """Calcula el offset para paginación."""
        return (self.page - 1) * self.limit


class AttendanceBulkResponse(BaseModel):
    """Respuesta al crear asistencias en lote."""

    created_count: int
    updated_count: int
