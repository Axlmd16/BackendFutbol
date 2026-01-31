"""Esquemas Pydantic para asistencias (creación/consulta/respuesta)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.base_schema import BaseSchema


class AttendanceItemCreate(BaseModel):
    """Registro de asistencia individual para un atleta."""

    athlete_id: int = Field(
        ...,
        ge=1,
        description="ID del atleta (debe ser mayor o igual a 1)",
    )
    is_present: bool = Field(default=True, description="¿Está presente?")
    justification: str | None = Field(
        default=None, max_length=500, description="Justificación si está ausente"
    )

    @field_validator("justification", mode="before")
    @classmethod
    def clean_justification(cls, value):
        """Limpia espacios en blanco de la justificación."""
        if value is not None and isinstance(value, str):
            value = value.strip()
            return value if value else None
        return value

    @model_validator(mode="after")
    def validate_justification_coherence(self):
        """Valida que la justificación sea None cuando is_present=True."""
        if self.is_present and self.justification:
            self.justification = None
        return self


class AttendanceBulkCreate(BaseModel):
    """Schema para crear múltiples registros de asistencia."""

    model_config = ConfigDict(str_strip_whitespace=True)

    attendance_date: date = Field(
        ...,
        alias="date",
        description="Fecha de la asistencia en formato YYYY-MM-DD. "
        "No se permiten fechas futuras.",
    )
    time: str | None = Field(
        default=None,
        description="Hora de la asistencia en formato HH:MM (ej: 08:30, 14:00). "
        "Si no se envía, se usa la hora actual del servidor.",
    )
    records: list[AttendanceItemCreate] = Field(
        ...,
        description="Lista de registros de asistencia. "
        "Debe contener al menos un registro.",
    )

    @field_validator("records", mode="after")
    @classmethod
    def validate_records_not_empty(cls, value):
        """Valida que la lista de registros no esté vacía."""
        if not value or len(value) == 0:
            raise ValueError(
                "La lista de registros no puede estar vacía. "
                "Debe incluir al menos un registro de asistencia."
            )
        return value

    @field_validator("attendance_date", mode="before")
    @classmethod
    def validate_date_format(cls, value):
        """Valida el formato de fecha y que no sea futura."""
        if isinstance(value, date):
            parsed_date = value
        elif isinstance(value, str):
            try:
                parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    "Formato de fecha inválido. Use el formato YYYY-MM-DD "
                    "(ejemplo: 2024-01-15)"
                ) from None
        else:
            raise ValueError(
                "Formato de fecha inválido. Use el formato YYYY-MM-DD "
                "(ejemplo: 2024-01-15)"
            )

        # Validar que no sea fecha futura
        if parsed_date > date.today():
            raise ValueError(
                "No se puede registrar asistencia para fechas futuras. "
                f"La fecha debe ser menor o igual a {date.today().strftime('%Y-%m-%d')}"
            )
        return parsed_date

    @field_validator("time", mode="before")
    @classmethod
    def validate_time_format(cls, value):
        """Valida el formato de hora HH:MM."""
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "Formato de hora inválido. Use el formato HH:MM (ejemplo: 08:30, 14:00)"
            )

        value = value.strip()
        if not value:
            return None

        import re

        pattern = r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
        if not re.match(pattern, value):
            raise ValueError(
                "Formato de hora inválido. Use el formato HH:MM "
                "(ejemplo: 08:30, 14:00). La hora debe estar entre 00:00 y 23:59"
            )
        return value


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
        ...,
        alias="date",
        description="Fecha de la asistencia en formato YYYY-MM-DD",
    )
    type_athlete: str | None = Field(
        default=None, description="Tipo de atleta para filtrar"
    )
    search: str | None = Field(default=None, description="Búsqueda por nombre o DNI")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)

    @field_validator("attendance_date", mode="before")
    @classmethod
    def validate_date_format(cls, value):
        """Valida el formato de fecha."""
        if isinstance(value, date):
            return value
        elif isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    "Formato de fecha inválido. Use el formato YYYY-MM-DD "
                    "(ejemplo: 2024-01-15)"
                ) from None
        else:
            raise ValueError(
                "Formato de fecha inválido. Use el formato YYYY-MM-DD "
                "(ejemplo: 2024-01-15)"
            )

    @property
    def skip(self) -> int:
        """Calcula el offset para paginación."""
        return (self.page - 1) * self.limit


class AttendanceBulkResponse(BaseModel):
    """Respuesta al crear asistencias en lote."""

    created_count: int
    updated_count: int
