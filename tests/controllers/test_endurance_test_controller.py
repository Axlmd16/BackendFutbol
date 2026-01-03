"""Tests unitarios para `EnduranceTestController`."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.endurance_test_controller import EnduranceTestController
from app.models.endurance_test import EnduranceTest
from app.models.evaluation import Evaluation
from app.utils.exceptions import DatabaseException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def endurance_test_controller():
    """Fixture para EnduranceTestController con DAOs mockeados."""
    controller = EnduranceTestController()
    controller.endurance_test_dao = MagicMock()
    controller.test_dao = MagicMock()
    controller.evaluation_dao = MagicMock()
    controller.athlete_dao = MagicMock()
    return controller


@pytest.fixture
def mock_db():
    """Mock de sesión de base de datos."""
    return MagicMock()


@pytest.fixture
def mock_evaluation():
    """Fixture de una evaluación mock."""
    evaluation = Mock(spec=Evaluation)
    evaluation.id = 1
    evaluation.name = "Evaluación Física"
    evaluation.is_active = True
    return evaluation


@pytest.fixture
def mock_athlete():
    """Fixture de un atleta mock."""
    athlete = Mock()
    athlete.id = 5
    athlete.name = "Juan Pérez"
    return athlete


@pytest.fixture
def mock_endurance_test():
    """Fixture de un Endurance Test mock."""
    test = Mock(spec=EnduranceTest)
    test.id = 3
    test.type = "endurance_test"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.min_duration = 36
    test.total_distance_m = 6000
    test.observations = "Good aerobic capacity"
    test.is_active = True
    return test


# ==============================================
# TESTS: ADD ENDURANCE TEST
# ==============================================


def test_add_endurance_test_success(
    endurance_test_controller,
    mock_db,
    mock_evaluation,
    mock_athlete,
    mock_endurance_test,
):
    """Agregar Endurance Test exitosamente."""
    endurance_test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    endurance_test_controller.athlete_dao.get_by_id.return_value = mock_athlete
    endurance_test_controller.test_dao.create_endurance_test.return_value = (
        mock_endurance_test
    )

    result = endurance_test_controller.add_test(
        db=mock_db,
        evaluation_id=1,
        athlete_id=5,
        date=mock_endurance_test.date,
        min_duration=36,
        total_distance_m=6000,
        observations="Good aerobic capacity",
    )

    assert result.id == 3
    assert result.type == "endurance_test"
    assert result.min_duration == 36
    assert result.total_distance_m == 6000
    endurance_test_controller.test_dao.create_endurance_test.assert_called_once()


def test_add_endurance_test_evaluation_not_found(endurance_test_controller, mock_db):
    """Agregar Endurance Test a evaluación inexistente."""
    endurance_test_controller.evaluation_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        endurance_test_controller.add_test(
            db=mock_db,
            evaluation_id=999,
            athlete_id=5,
            date=datetime.now(),
            min_duration=36,
            total_distance_m=6000,
        )


def test_add_endurance_test_athlete_not_found(
    endurance_test_controller, mock_db, mock_evaluation
):
    """Agregar Endurance Test a atleta inexistente."""
    endurance_test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    endurance_test_controller.athlete_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Atleta 999 no existe"):
        endurance_test_controller.add_test(
            db=mock_db,
            evaluation_id=1,
            athlete_id=999,
            date=datetime.now(),
            min_duration=36,
            total_distance_m=6000,
        )


# ==============================================
# TESTS: UPDATE ENDURANCE TEST
# ==============================================


def test_update_endurance_test_success(
    endurance_test_controller, mock_db, mock_endurance_test
):
    """Actualizar un Endurance Test existente."""
    endurance_test_controller.endurance_test_dao.get_by_id.return_value = (
        mock_endurance_test
    )
    updated = Mock()
    updated.id = mock_endurance_test.id
    updated.total_distance_m = 6200
    endurance_test_controller.endurance_test_dao.update.return_value = updated

    result = endurance_test_controller.update_test(
        db=mock_db, test_id=3, total_distance_m=6200, observations="Subió el ritmo"
    )

    assert result.total_distance_m == 6200
    endurance_test_controller.endurance_test_dao.update.assert_called_once_with(
        mock_db, 3, {"total_distance_m": 6200, "observations": "Subió el ritmo"}
    )


def test_update_endurance_test_not_found(endurance_test_controller, mock_db):
    """Retorna None si el Endurance Test no existe."""
    endurance_test_controller.endurance_test_dao.get_by_id.return_value = None

    result = endurance_test_controller.update_test(db=mock_db, test_id=999)

    assert result is None
    endurance_test_controller.endurance_test_dao.update.assert_not_called()


def test_update_endurance_test_evaluation_not_found(endurance_test_controller, mock_db):
    """Valida evaluación al actualizar."""
    endurance_test_controller.evaluation_dao.get_by_id.return_value = None
    endurance_test_controller.endurance_test_dao.get_by_id.return_value = Mock()

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        endurance_test_controller.update_test(
            db=mock_db, test_id=3, evaluation_id=999, min_duration=40
        )


def test_update_endurance_test_athlete_not_found(endurance_test_controller, mock_db):
    """Valida atleta al actualizar."""
    endurance_test_controller.evaluation_dao.get_by_id.return_value = Mock()
    endurance_test_controller.athlete_dao.get_by_id.return_value = None
    endurance_test_controller.endurance_test_dao.get_by_id.return_value = Mock()

    with pytest.raises(DatabaseException, match="Atleta 888 no existe"):
        endurance_test_controller.update_test(
            db=mock_db, test_id=3, athlete_id=888, min_duration=40
        )


def test_update_endurance_test_no_fields_returns_existing(
    endurance_test_controller, mock_db, mock_endurance_test
):
    """Sin campos a actualizar devuelve la entidad actual."""
    endurance_test_controller.endurance_test_dao.get_by_id.return_value = (
        mock_endurance_test
    )

    result = endurance_test_controller.update_test(db=mock_db, test_id=3)

    assert result is mock_endurance_test
    endurance_test_controller.endurance_test_dao.update.assert_not_called()
