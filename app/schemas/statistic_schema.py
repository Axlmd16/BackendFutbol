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


class AthleteTestSummary(BaseModel):
    """Resumen de tests de un atleta."""

    test_type: str
    count: int
    avg_score: Optional[float] = None
    last_date: Optional[str] = None


class AthleteIndividualStatsResponse(BaseModel):
    """Estadísticas individuales de un atleta."""

    # Información básica del atleta
    athlete_id: int
    athlete_name: str
    type_athlete: str
    sex: str
    is_active: bool

    # Estadísticas físicas (del modelo Statistic)
    speed: Optional[float] = None
    stamina: Optional[float] = None
    strength: Optional[float] = None
    agility: Optional[float] = None

    # Estadísticas de rendimiento deportivo
    matches_played: int = 0
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0

    # Resumen de asistencia
    attendance_total: int = 0
    attendance_present: int = 0
    attendance_absent: int = 0
    attendance_rate: float = 0.0

    # Resumen de tests
    tests_completed: int = 0
    tests_by_type: List[AthleteTestSummary] = []


class UpdateSportsStatsRequest(BaseModel):
    """Request para actualizar estadísticas deportivas de un atleta."""

    matches_played: Optional[int] = Field(None, ge=0, description="Partidos jugados")
    goals: Optional[int] = Field(None, ge=0, description="Goles")
    assists: Optional[int] = Field(None, ge=0, description="Asistencias")
    yellow_cards: Optional[int] = Field(None, ge=0, description="Tarjetas amarillas")
    red_cards: Optional[int] = Field(None, ge=0, description="Tarjetas rojas")


class TestHistoryEntry(BaseModel):
    """Un registro individual del historial de tests."""

    id: int
    test_type: str
    date: str
    raw_value: Optional[float] = None
    raw_unit: Optional[str] = None
    score: float  # Score normalizado 0-100


class AthleteTestsHistoryResponse(BaseModel):
    """Historial completo de tests de un atleta para gráficos de progreso."""

    athlete_id: int
    athlete_name: str
    tests_history: List[TestHistoryEntry] = []
    # Estadísticas agregadas por tipo para resumen
    summary_by_type: dict = {}
