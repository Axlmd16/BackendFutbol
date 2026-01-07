"""Tests unitarios para validaciones en StatisticDAO."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.dao.statistic_dao import StatisticDAO
from app.utils.exceptions import DatabaseException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def statistic_dao():
    """Fixture para StatisticDAO."""
    return StatisticDAO()


@pytest.fixture
def mock_db():
    """Mock de sesión de base de datos."""
    return MagicMock()


# ==============================================
# TESTS: VALIDACIONES TEMPORALES
# ==============================================


def test_attendance_stats_start_date_after_end_date_rejected(statistic_dao, mock_db):
    """Validación: start_date posterior a end_date debe ser rechazado."""
    start_date = date.today()
    end_date = start_date - timedelta(days=10)

    with pytest.raises(DatabaseException) as exc_info:
        statistic_dao.get_attendance_stats(
            db=mock_db,
            start_date=start_date,
            end_date=end_date,
        )

    assert "Error al obtener estadísticas de asistencia" in str(exc_info.value)


def test_attendance_stats_valid_date_range(statistic_dao, mock_db):
    """Validación: Rango de fechas válido."""
    start_date = date.today() - timedelta(days=30)
    end_date = date.today()

    # Configurar mocks
    mock_query = MagicMock()
    mock_filter = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0

    # No debe lanzar excepción
    result = statistic_dao.get_attendance_stats(
        db=mock_db,
        start_date=start_date,
        end_date=end_date,
    )

    assert isinstance(result, dict)


def test_attendance_stats_same_date_valid(statistic_dao, mock_db):
    """Validación: Misma fecha para inicio y fin es válida."""
    same_date = date.today()

    # Configurar mocks
    mock_query = MagicMock()
    mock_filter = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0

    # No debe lanzar excepción
    result = statistic_dao.get_attendance_stats(
        db=mock_db,
        start_date=same_date,
        end_date=same_date,
    )

    assert isinstance(result, dict)


def test_attendance_stats_only_start_date_valid(statistic_dao, mock_db):
    """Validación: Solo start_date sin end_date es válido."""
    start_date = date.today() - timedelta(days=30)

    # Configurar mocks
    mock_query = MagicMock()
    mock_filter = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0

    # No debe lanzar excepción
    result = statistic_dao.get_attendance_stats(
        db=mock_db,
        start_date=start_date,
        end_date=None,
    )

    assert isinstance(result, dict)


def test_attendance_stats_only_end_date_valid(statistic_dao, mock_db):
    """Validación: Solo end_date sin start_date es válido."""
    end_date = date.today()

    # Configurar mocks
    mock_query = MagicMock()
    mock_filter = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.count.return_value = 0

    # No debe lanzar excepción
    result = statistic_dao.get_attendance_stats(
        db=mock_db,
        start_date=None,
        end_date=end_date,
    )

    assert isinstance(result, dict)


def test_attendance_stats_no_dates_valid(statistic_dao, mock_db):
    """Validación: Sin fechas es válido (consulta todos los registros)."""
    # Configurar mocks
    mock_query = MagicMock()
    mock_filter = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.count.return_value = 0

    # No debe lanzar excepción
    result = statistic_dao.get_attendance_stats(
        db=mock_db,
        start_date=None,
        end_date=None,
    )

    assert isinstance(result, dict)
