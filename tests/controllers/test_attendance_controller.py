"""Tests unitarios para `AttendanceController`."""

from datetime import date, datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.attendance_controller import AttendanceController
from app.models.athlete import Athlete
from app.models.attendance import Attendance
from app.schemas.attendance_schema import AttendanceBulkCreate, AttendanceFilter

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def attendance_controller():
    """Fixture para AttendanceController con DAO mockeado."""
    controller = AttendanceController()
    controller.attendance_dao = MagicMock()
    return controller


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
    athlete.is_active = True
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
    attendance.created_at = datetime.now()
    return attendance


@pytest.fixture
def mock_attendance_absent(mock_athlete):
    """Fixture de una asistencia de ausente mock."""
    attendance = Mock(spec=Attendance)
    attendance.id = 2
    attendance.date = datetime(2025, 12, 30)
    attendance.time = "10:30"
    attendance.is_present = False
    attendance.justification = "Enfermedad"
    attendance.athlete_id = 1
    attendance.athlete = mock_athlete
    attendance.user_dni = "1150696977"
    attendance.is_active = True
    attendance.created_at = datetime.now()
    return attendance


# ==============================================
# TESTS: CREATE BULK ATTENDANCE
# ==============================================


def test_create_bulk_attendance_success(attendance_controller, mock_db):
    """Crear asistencias en lote exitosamente."""
    attendance_controller.attendance_dao.create_or_update_bulk.return_value = (3, 0)

    data = AttendanceBulkCreate(
        date=date(2025, 12, 30),
        time="10:30",
        records=[
            {"athlete_id": 1, "is_present": True},
            {"athlete_id": 2, "is_present": True},
            {"athlete_id": 3, "is_present": False, "justification": "Enfermo"},
        ],
    )

    created, updated = attendance_controller.create_bulk_attendance(
        db=mock_db, data=data, user_dni="1150696977"
    )

    assert created == 3
    assert updated == 0
    attendance_controller.attendance_dao.create_or_update_bulk.assert_called_once()


def test_create_bulk_attendance_without_time(attendance_controller, mock_db):
    """Crear asistencias sin hora usa hora actual."""
    attendance_controller.attendance_dao.create_or_update_bulk.return_value = (2, 0)

    data = AttendanceBulkCreate(
        date=date(2025, 12, 30),
        time=None,  # Sin hora
        records=[
            {"athlete_id": 1, "is_present": True},
            {"athlete_id": 2, "is_present": True},
        ],
    )

    created, updated = attendance_controller.create_bulk_attendance(
        db=mock_db, data=data, user_dni="1150696977"
    )

    assert created == 2
    # Verificar que se llamó con una hora (la actual)
    call_args = attendance_controller.attendance_dao.create_or_update_bulk.call_args
    assert call_args.kwargs["time_str"] is not None


def test_create_bulk_attendance_update_existing(attendance_controller, mock_db):
    """Actualizar asistencias existentes."""
    attendance_controller.attendance_dao.create_or_update_bulk.return_value = (0, 3)

    data = AttendanceBulkCreate(
        date=date(2025, 12, 30),
        time="11:00",
        records=[
            {"athlete_id": 1, "is_present": True},
            {"athlete_id": 2, "is_present": False},
            {"athlete_id": 3, "is_present": True},
        ],
    )

    created, updated = attendance_controller.create_bulk_attendance(
        db=mock_db, data=data, user_dni="1150696977"
    )

    assert created == 0
    assert updated == 3


def test_create_bulk_attendance_empty_records_success(attendance_controller, mock_db):
    """Crear asistencias con lista vacía (limpiar día) es válido."""
    attendance_controller.attendance_dao.create_or_update_bulk.return_value = (0, 0)

    data = AttendanceBulkCreate(
        date=date(2025, 12, 30),
        time="10:30",
        records=[],
    )

    created, updated = attendance_controller.create_bulk_attendance(
        db=mock_db, data=data, user_dni="1150696977"
    )

    assert created == 0
    assert updated == 0
    attendance_controller.attendance_dao.create_or_update_bulk.assert_called_once()


def test_create_bulk_attendance_invalid_time_format_raises_error():
    """Hora con formato inválido lanza error."""
    with pytest.raises(ValueError):
        AttendanceBulkCreate(
            date=date(2025, 12, 30),
            time="25:00",  # Hora inválida
            records=[{"athlete_id": 1, "is_present": True}],
        )


# ==============================================
# TESTS: GET ATTENDANCES BY DATE
# ==============================================


def test_get_attendances_by_date_success(
    attendance_controller, mock_db, mock_attendance
):
    """Obtener asistencias por fecha exitosamente."""
    attendance_controller.attendance_dao.get_by_date.return_value = (
        [mock_attendance],
        1,
    )

    filters = AttendanceFilter(date=date(2025, 12, 30))

    items, total = attendance_controller.get_attendances_by_date(
        db=mock_db, filters=filters
    )

    assert total == 1
    assert len(items) == 1
    assert items[0]["id"] == 1
    assert items[0]["athlete_name"] == "Juan Pérez"
    attendance_controller.attendance_dao.get_by_date.assert_called_once()


def test_get_attendances_by_date_empty(attendance_controller, mock_db):
    """Obtener asistencias cuando no hay registros."""
    attendance_controller.attendance_dao.get_by_date.return_value = ([], 0)

    filters = AttendanceFilter(date=date(2025, 12, 30))

    items, total = attendance_controller.get_attendances_by_date(
        db=mock_db, filters=filters
    )

    assert total == 0
    assert len(items) == 0


def test_get_attendances_by_date_with_type_filter(
    attendance_controller, mock_db, mock_attendance
):
    """Obtener asistencias filtradas por tipo de atleta."""
    attendance_controller.attendance_dao.get_by_date.return_value = (
        [mock_attendance],
        1,
    )

    filters = AttendanceFilter(date=date(2025, 12, 30), type_athlete="DOCENTES")

    items, total = attendance_controller.get_attendances_by_date(
        db=mock_db, filters=filters
    )

    assert total == 1
    call_args = attendance_controller.attendance_dao.get_by_date.call_args
    assert call_args.kwargs["type_athlete"] == "DOCENTES"


def test_get_attendances_by_date_with_search(
    attendance_controller, mock_db, mock_attendance
):
    """Obtener asistencias con búsqueda por nombre o DNI."""
    attendance_controller.attendance_dao.get_by_date.return_value = (
        [mock_attendance],
        1,
    )

    filters = AttendanceFilter(date=date(2025, 12, 30), search="Juan")

    items, total = attendance_controller.get_attendances_by_date(
        db=mock_db, filters=filters
    )

    assert total == 1
    call_args = attendance_controller.attendance_dao.get_by_date.call_args
    assert call_args.kwargs["search"] == "Juan"


def test_get_attendances_by_date_pagination(attendance_controller, mock_db):
    """Verificar que la paginación se aplica correctamente."""
    attendance_controller.attendance_dao.get_by_date.return_value = ([], 0)

    filters = AttendanceFilter(date=date(2025, 12, 30), page=2, limit=10)

    attendance_controller.get_attendances_by_date(db=mock_db, filters=filters)

    call_args = attendance_controller.attendance_dao.get_by_date.call_args
    assert call_args.kwargs["skip"] == 10  # (page 2 - 1) * 10
    assert call_args.kwargs["limit"] == 10


# ==============================================
# TESTS: GET ATTENDANCE SUMMARY
# ==============================================


def test_get_attendance_summary_success(attendance_controller, mock_db):
    """Obtener resumen de asistencia exitosamente."""
    attendance_controller.attendance_dao.get_attendance_summary_by_date.return_value = {
        "total": 50,
        "present": 45,
        "absent": 5,
    }

    result = attendance_controller.get_attendance_summary(
        db=mock_db, target_date=date(2025, 12, 30)
    )

    assert result["total"] == 50
    assert result["present"] == 45
    assert result["absent"] == 5


def test_get_attendance_summary_no_records(attendance_controller, mock_db):
    """Obtener resumen cuando no hay registros."""
    attendance_controller.attendance_dao.get_attendance_summary_by_date.return_value = {
        "total": 0,
        "present": 0,
        "absent": 0,
    }

    result = attendance_controller.get_attendance_summary(
        db=mock_db, target_date=date(2025, 12, 30)
    )

    assert result["total"] == 0
    assert result["present"] == 0
    assert result["absent"] == 0


# ==============================================
# TESTS: RESPONSE FORMATTING
# ==============================================


def test_format_attendance_response_present(
    attendance_controller, mock_db, mock_attendance
):
    """Verificar formato de respuesta para asistencia presente."""
    attendance_controller.attendance_dao.get_by_date.return_value = (
        [mock_attendance],
        1,
    )

    filters = AttendanceFilter(date=date(2025, 12, 30))
    items, _ = attendance_controller.get_attendances_by_date(
        db=mock_db, filters=filters
    )

    item = items[0]
    assert item["is_present"] is True
    assert item["justification"] is None
    assert item["athlete_dni"] == "1234567890"
    assert item["athlete_type"] == "DOCENTES"


def test_format_attendance_response_absent(
    attendance_controller, mock_db, mock_attendance_absent
):
    """Verificar formato de respuesta para asistencia ausente."""
    attendance_controller.attendance_dao.get_by_date.return_value = (
        [mock_attendance_absent],
        1,
    )

    filters = AttendanceFilter(date=date(2025, 12, 30))
    items, _ = attendance_controller.get_attendances_by_date(
        db=mock_db, filters=filters
    )

    item = items[0]
    assert item["is_present"] is False
    assert item["justification"] == "Enfermedad"
