"""Esquemas Pydantic para reportes deportivos."""

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.athlete_schema import SexInput
from app.schemas.base_schema import BaseSchema
from app.schemas.user_schema import TypeStament


class ReportType(str, Enum):
    """Tipos de reportes disponibles."""

    ATTENDANCE = "attendance"
    TESTS = "tests"
    STATISTICS = "statistics"


class ReportFilter(BaseModel):
    """Filtros para generación de reportes."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    # Tipo y formato
    report_type: Optional[ReportType] = Field(
        default=None, description="Tipo de reporte específico"
    )
    format: Literal["pdf", "xlsx", "csv"] = Field(
        default="pdf",
        description="Formato de exportación",
    )

    # Filtros temporales
    start_date: Optional[date] = Field(None, description="Fecha inicio (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="Fecha fin (YYYY-MM-DD)")

    # Filtros de atletas
    athlete_id: Optional[int] = Field(None, description="ID del deportista específico")
    athlete_type: Optional[TypeStament] = Field(None, description="Tipo de deportista")
    sex: Optional[SexInput] = Field(None, description="Sexo")


class ReportMetadata(BaseModel):
    """Metadata formal para reportes."""

    title: str = Field(..., description="Título del reporte")
    system_name: str = Field(
        default="Sistema Kallpa UNL", description="Nombre del sistema"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de generación"
    )
    generated_by: str = Field(..., description="Usuario que generó el reporte")
    filters_applied: dict = Field(
        default_factory=dict, description="Filtros aplicados al reporte"
    )
    period: Optional[str] = Field(
        None, description="Período del reporte (ej: Enero 2025)"
    )


class AttendanceReportData(BaseSchema):
    """Datos de asistencia para reporte."""

    athlete_id: int
    athlete_name: str
    athlete_type: str
    total_sessions: int
    attended_sessions: int
    attendance_percentage: float


class TestReportData(BaseSchema):
    """Datos de tests para reporte."""

    athlete_id: int
    athlete_name: str
    test_type: str
    test_date: date
    result_value: Optional[float] = None
    result_unit: Optional[str] = None


class StatisticsReportData(BaseSchema):
    """Datos de estadísticas para reporte."""

    metric_name: str
    metric_value: float
    metric_unit: Optional[str] = None
    category: Optional[str] = None


class ReportGenerationResponse(BaseSchema):
    """Respuesta de generación de reporte."""

    report_id: str
    format: str
    file_name: str
    file_size: Optional[int] = None
    generated_at: str
    download_url: Optional[str] = None
