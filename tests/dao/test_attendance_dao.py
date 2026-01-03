"""Tests unitarios para `AttendanceDAO`."""

from datetime import date, datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.dao.attendance_dao import AttendanceDAO
from app.models.athlete import Athlete
from app.models.attendance import Attendance
from app.utils.exceptions import DatabaseException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def attendance_dao():
    """Fixture para AttendanceDAO."""
    return AttendanceDAO()


@pytest.fixture
def mock_db():
    """Mock de sesión de base de datos."""
    return MagicMock()


@pytest.fixture
def mock_athlete():
    """Fixture de un atleta mock."""
    athlete = Mock(spec=Athlete)
    athlete.id = 1
    athlete.full_name = "Juan Pérez"
    athlete.dni = "1234567890"
    athlete.type_athlete = "DOCENTES"
    return athlete


@pytest.fixture
def mock_attendance(mock_athlete):
    """Fixture de una asistencia mock."""
    attendance = Mock(spec=Attendance)
    attendance.id = 1
    attendance.date = datetime(2025, 12, 30)
    attendance.time = "10:30"
    attendance.is_present = True
    attendance.justification = None
    attendance.athlete_id = 1
    attendance.athlete = mock_athlete
    attendance.user_dni = "1150696977"
    attendance.is_active = True
    return attendance


# ==============================================
# TESTS: GET BY DATE
# ==============================================


def test_get_by_date_success(attendance_dao, mock_db, mock_attendance):
    """Obtener asistencias por fecha exitosamente."""
    # Setup mock query
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [mock_attendance]
    mock_db.query.return_value = mock_query

    items, total = attendance_dao.get_by_date(
        db=mock_db,
        target_date=date(2025, 12, 30),
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].id == 1


def test_get_by_date_with_type_filter(attendance_dao, mock_db, mock_attendance):
    """Obtener asistencias filtradas por tipo de atleta."""
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [mock_attendance]
    mock_db.query.return_value = mock_query

    items, total = attendance_dao.get_by_date(
        db=mock_db,
        target_date=date(2025, 12, 30),
        type_athlete="DOCENTES",
    )

    assert total == 1
    # Verificamos que se aplicó el filtro
    assert mock_query.filter.call_count >= 2  # Base filter + type filter


def test_get_by_date_with_search(attendance_dao, mock_db, mock_attendance):
    """Obtener asistencias con búsqueda por nombre o DNI."""
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [mock_attendance]
    mock_db.query.return_value = mock_query

    items, total = attendance_dao.get_by_date(
        db=mock_db,
        target_date=date(2025, 12, 30),
        search="Juan",
    )

    assert total == 1


def test_get_by_date_empty(attendance_dao, mock_db):
    """Obtener asistencias cuando no hay registros."""
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 0
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    mock_db.query.return_value = mock_query

    items, total = attendance_dao.get_by_date(
        db=mock_db,
        target_date=date(2025, 12, 30),
    )

    assert total == 0
    assert len(items) == 0


def test_get_by_date_pagination(attendance_dao, mock_db):
    """Verificar que la paginación se aplica correctamente."""
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 0
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    mock_db.query.return_value = mock_query

    attendance_dao.get_by_date(
        db=mock_db,
        target_date=date(2025, 12, 30),
        skip=10,
        limit=25,
    )

    mock_query.offset.assert_called_with(10)
    mock_query.limit.assert_called_with(25)


# ==============================================
# TESTS: GET BY ATHLETE AND DATE
# ==============================================


def test_get_by_athlete_and_date_found(attendance_dao, mock_db, mock_attendance):
    """Encontrar asistencia existente para atleta y fecha."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_attendance
    mock_db.query.return_value = mock_query

    result = attendance_dao.get_by_athlete_and_date(
        db=mock_db,
        athlete_id=1,
        target_date=date(2025, 12, 30),
    )

    assert result is not None
    assert result.id == 1
    assert result.athlete_id == 1


def test_get_by_athlete_and_date_not_found(attendance_dao, mock_db):
    """No encontrar asistencia para atleta y fecha."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query

    result = attendance_dao.get_by_athlete_and_date(
        db=mock_db,
        athlete_id=999,
        target_date=date(2025, 12, 30),
    )

    assert result is None


# ==============================================
# TESTS: CREATE OR UPDATE BULK
# ==============================================


def test_create_bulk_success(attendance_dao, mock_db):
    """Crear asistencias en lote exitosamente."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None  # No existe, crear nuevo
    mock_db.query.return_value = mock_query

    records = [
        {"athlete_id": 1, "is_present": True, "justification": None},
        {"athlete_id": 2, "is_present": True, "justification": None},
        {"athlete_id": 3, "is_present": False, "justification": "Enfermo"},
    ]

    created, updated = attendance_dao.create_or_update_bulk(
        db=mock_db,
        target_date=date(2025, 12, 30),
        time_str="10:30",
        user_dni="1150696977",
        records=records,
    )

    assert created == 3
    assert updated == 0
    assert mock_db.add.call_count == 3
    mock_db.commit.assert_called_once()


def test_update_bulk_success(attendance_dao, mock_db, mock_attendance):
    """Actualizar asistencias existentes en lote."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_attendance  # Existe, actualizar
    mock_db.query.return_value = mock_query

    records = [
        {"athlete_id": 1, "is_present": False, "justification": "Viaje"},
    ]

    created, updated = attendance_dao.create_or_update_bulk(
        db=mock_db,
        target_date=date(2025, 12, 30),
        time_str="11:00",
        user_dni="1150696977",
        records=records,
    )

    assert created == 0
    assert updated == 1
    assert mock_attendance.time == "11:00"
    assert mock_attendance.is_present is False


def test_create_bulk_clears_justification_when_present(attendance_dao, mock_db):
    """Verificar que la justificación se limpia cuando está presente."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query

    records = [
        {
            "athlete_id": 1,
            "is_present": True,
            "justification": "Esta justificación debe limpiarse",
        },
    ]

    created, updated = attendance_dao.create_or_update_bulk(
        db=mock_db,
        target_date=date(2025, 12, 30),
        time_str="10:30",
        user_dni="1150696977",
        records=records,
    )

    # Verificar que se llamó add con justificación None
    call_args = mock_db.add.call_args
    added_attendance = call_args[0][0]
    assert added_attendance.justification is None


def test_create_bulk_rollback_on_error(attendance_dao, mock_db):
    """Verificar rollback cuando ocurre un error."""
    mock_query = MagicMock()
    mock_query.filter.side_effect = Exception("Database error")
    mock_db.query.return_value = mock_query

    records = [{"athlete_id": 1, "is_present": True}]

    with pytest.raises(DatabaseException):
        attendance_dao.create_or_update_bulk(
            db=mock_db,
            target_date=date(2025, 12, 30),
            time_str="10:30",
            user_dni="1150696977",
            records=records,
        )

    mock_db.rollback.assert_called_once()


# ==============================================
# TESTS: GET ATTENDANCE SUMMARY
# ==============================================


def test_get_attendance_summary_success(attendance_dao, mock_db):
    """Obtener resumen de asistencia exitosamente."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query

    # Mock para total y present
    mock_query.scalar.side_effect = [50, 45]  # total=50, present=45
    mock_db.query.return_value = mock_query

    result = attendance_dao.get_attendance_summary_by_date(
        db=mock_db,
        target_date=date(2025, 12, 30),
    )

    assert result["total"] == 50
    assert result["present"] == 45
    assert result["absent"] == 5


def test_get_attendance_summary_empty(attendance_dao, mock_db):
    """Obtener resumen cuando no hay registros."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.scalar.side_effect = [0, 0]  # total=0, present=0
    mock_db.query.return_value = mock_query

    result = attendance_dao.get_attendance_summary_by_date(
        db=mock_db,
        target_date=date(2025, 12, 30),
    )

    assert result["total"] == 0
    assert result["present"] == 0
    assert result["absent"] == 0


def test_get_attendance_summary_handles_none(attendance_dao, mock_db):
    """Manejar valores None en el resumen."""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.scalar.side_effect = [None, None]  # Null values
    mock_db.query.return_value = mock_query

    result = attendance_dao.get_attendance_summary_by_date(
        db=mock_db,
        target_date=date(2025, 12, 30),
    )

    # Debe manejar None y retornar 0
    assert result["total"] == 0
    assert result["present"] == 0
    assert result["absent"] == 0
