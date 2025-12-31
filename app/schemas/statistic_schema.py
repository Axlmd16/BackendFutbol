"""
Schemas para el módulo de estadísticas.

Define los modelos Pydantic para filtros y respuestas de estadísticas.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class StatisticFilter(BaseModel):
    """Filtros para consultas de estadísticas."""

    start_date: Optional[date] = Field(None, description="Fecha de inicio")
    end_date: Optional[date] = Field(None, description="Fecha de fin")
    type_athlete: Optional[str] = Field(None, description="Tipo de atleta")
    sex: Optional[str] = Field(None, description="Sexo (MALE, FEMALE)")
    athlete_id: Optional[int] = Field(None, description="ID de atleta específico")


class AthleteTypeDistribution(BaseModel):
    """Distribución de atletas por tipo."""

    type_athlete: str
    count: int
    percentage: float


class GenderDistribution(BaseModel):
    """Distribución de atletas por género."""

    sex: str
    count: int
    percentage: float


class ClubOverviewResponse(BaseModel):
    """Métricas generales del club."""

    total_athletes: int
    active_athletes: int
    inactive_athletes: int
    athletes_by_type: List[AthleteTypeDistribution]
    athletes_by_gender: List[GenderDistribution]
    total_evaluations: int
    total_tests: int


class AttendancePeriodStats(BaseModel):
    """Estadísticas de asistencia por periodo."""

    date: str
    present_count: int
    absent_count: int
    attendance_rate: float


class AttendanceStatsResponse(BaseModel):
    """Estadísticas de asistencia."""

    total_records: int
    total_present: int
    total_absent: int
    overall_attendance_rate: float
    attendance_by_period: List[AttendancePeriodStats]
    attendance_by_type: List[dict]


class TestTypeStats(BaseModel):
    """Estadísticas por tipo de test."""

    test_type: str
    total_tests: int
    avg_score: Optional[float]
    min_score: Optional[float]
    max_score: Optional[float]


class TopPerformer(BaseModel):
    """Atleta con mejor rendimiento."""

    athlete_id: int
    athlete_name: str
    athlete_type: Optional[str]
    avg_score: float
    tests_completed: int


class TestPerformanceResponse(BaseModel):
    """Estadísticas de rendimiento en tests."""

    total_tests: int
    tests_by_type: List[TestTypeStats]
    top_performers: List[TopPerformer]
