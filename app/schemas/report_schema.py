"""Esquemas Pydantic para reportes deportivos."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base_schema import BaseSchema


class ReportFilter(BaseModel):
    """Filtros para generación de reportes."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    club_id: Optional[int] = Field(None, description="ID del club/escuela")
    athlete_id: Optional[int] = Field(None, description="ID del deportista")
    start_date: Optional[date] = Field(None, description="Fecha inicio (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="Fecha fin (YYYY-MM-DD)")
    include_attendance: bool = Field(
        default=True, description="Incluir datos de asistencia"
    )
    include_evaluations: bool = Field(
        default=True, description="Incluir datos de evaluaciones"
    )
    include_tests: bool = Field(
        default=True, description="Incluir resultados de pruebas"
    )
    format: str = Field(
        default="xlsx",
        description="Formato: pdf, csv, xlsx",
        pattern="^(?i)(pdf|csv|xlsx)$",  # permite mayúsculas y minúsculas
    )
    report_type: str = Field(
        default="all",
        description="Tipo de reporte: attendance, evaluation, results, all",
    )


class AttendanceReportData(BaseSchema):
    """Datos de asistencia para reporte."""

    athlete_id: int
    athlete_name: str
    attendance_date: date
    attendance_time: Optional[str] = None
    attendance_status: str  # PRESENT, ABSENT, LATE


class EvaluationReportData(BaseSchema):
    """Datos de evaluación para reporte."""

    athlete_id: int
    athlete_name: str
    evaluation_date: date
    evaluation_type: str
    score: Optional[float] = None
    comments: Optional[str] = None


class TestResultReportData(BaseSchema):
    """Datos de resultados de pruebas para reporte."""

    athlete_id: int
    athlete_name: str
    test_date: date
    test_type: str  # SPRINT, ENDURANCE, YOYO, TECHNICAL_ASSESSMENT
    result: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None


class ReportGenerationResponse(BaseSchema):
    """Respuesta de generación de reporte."""

    report_id: str
    format: str
    file_name: str
    file_size: Optional[int] = None
    generated_at: str
    expires_at: Optional[str] = None
    download_url: Optional[str] = None


class ReportSummary(BaseSchema):
    """Resumen de reporte generado."""

    total_athletes: int
    total_attendance_records: int
    total_evaluations: int
    total_tests: int
    date_range: str
    generated_by_user: str
    generated_at: str
