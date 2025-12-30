"""Tests unitarios para `SprintTestController`."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.sprint_test_controller import SprintTestController
from app.models.evaluation import Evaluation
from app.models.sprint_test import SprintTest
from app.utils.exceptions import DatabaseException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def sprint_test_controller():
    """Fixture para SprintTestController con DAOs mockeados."""
    controller = SprintTestController()
    controller.sprint_test_dao = MagicMock()
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
def mock_sprint_test():
    """Fixture de un Sprint Test mock."""
    test = Mock(spec=SprintTest)
    test.id = 1
    test.type = "sprint_test"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.distance_meters = 30
    test.time_0_10_s = 1.85
    test.time_0_30_s = 3.95
    test.observations = "Good performance"
    test.is_active = True
    return test


# ==============================================
# TESTS: ADD SPRINT TEST
# ==============================================


def test_add_sprint_test_success(
    sprint_test_controller, mock_db, mock_evaluation, mock_athlete, mock_sprint_test
):
    """Agregar Sprint Test exitosamente."""
    sprint_test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    sprint_test_controller.athlete_dao.get_by_id.return_value = mock_athlete
    sprint_test_controller.test_dao.create_sprint_test.return_value = mock_sprint_test

    result = sprint_test_controller.add_test(
        db=mock_db,
        evaluation_id=1,
        athlete_id=5,
        date=mock_sprint_test.date,
        distance_meters=30,
        time_0_10_s=1.85,
        time_0_30_s=3.95,
        observations="Good performance",
    )

    assert result.id == 1
    assert result.type == "sprint_test"
    assert result.distance_meters == 30
    sprint_test_controller.test_dao.create_sprint_test.assert_called_once()


def test_add_sprint_test_evaluation_not_found(sprint_test_controller, mock_db):
    """Agregar Sprint Test a evaluación inexistente."""
    sprint_test_controller.evaluation_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        sprint_test_controller.add_test(
            db=mock_db,
            evaluation_id=999,
            athlete_id=5,
            date=datetime.now(),
            distance_meters=30,
            time_0_10_s=1.85,
            time_0_30_s=3.95,
        )


def test_add_sprint_test_athlete_not_found(
    sprint_test_controller, mock_db, mock_evaluation
):
    """Agregar Sprint Test a atleta inexistente."""
    sprint_test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    sprint_test_controller.athlete_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Atleta 999 no existe"):
        sprint_test_controller.add_test(
            db=mock_db,
            evaluation_id=1,
            athlete_id=999,
            date=datetime.now(),
            distance_meters=30,
            time_0_10_s=1.85,
            time_0_30_s=3.95,
        )


# ==============================================
# TESTS: UPDATE SPRINT TEST
# ==============================================


def test_update_sprint_test_success(sprint_test_controller, mock_db, mock_sprint_test):
    """Actualizar campos de un Sprint Test existente."""
    sprint_test_controller.sprint_test_dao.get_by_id.return_value = mock_sprint_test
    updated = Mock()
    updated.id = mock_sprint_test.id
    updated.time_0_30_s = 3.80
    sprint_test_controller.sprint_test_dao.update.return_value = updated

    result = sprint_test_controller.update_test(
        db=mock_db, test_id=1, time_0_30_s=3.80, observations="Mejoró salida"
    )

    assert result.time_0_30_s == 3.80
    sprint_test_controller.sprint_test_dao.update.assert_called_once_with(
        mock_db, 1, {"time_0_30_s": 3.80, "observations": "Mejoró salida"}
    )


def test_update_sprint_test_not_found(sprint_test_controller, mock_db):
    """Retorna None si el Sprint Test no existe."""
    sprint_test_controller.sprint_test_dao.get_by_id.return_value = None

    result = sprint_test_controller.update_test(db=mock_db, test_id=999)

    assert result is None
    sprint_test_controller.sprint_test_dao.update.assert_not_called()


def test_update_sprint_test_evaluation_not_found(sprint_test_controller, mock_db):
    """Valida evaluación al actualizar."""
    sprint_test_controller.evaluation_dao.get_by_id.return_value = None
    sprint_test_controller.sprint_test_dao.get_by_id.return_value = Mock()

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        sprint_test_controller.update_test(
            db=mock_db, test_id=1, evaluation_id=999, distance_meters=40
        )


def test_update_sprint_test_athlete_not_found(sprint_test_controller, mock_db):
    """Valida atleta al actualizar."""
    sprint_test_controller.evaluation_dao.get_by_id.return_value = Mock()
    sprint_test_controller.athlete_dao.get_by_id.return_value = None
    sprint_test_controller.sprint_test_dao.get_by_id.return_value = Mock()

    with pytest.raises(DatabaseException, match="Atleta 888 no existe"):
        sprint_test_controller.update_test(
            db=mock_db, test_id=1, athlete_id=888, distance_meters=40
        )


def test_update_sprint_test_no_fields_returns_existing(
    sprint_test_controller, mock_db, mock_sprint_test
):
    """Si no se envían campos, se retorna la instancia actual."""
    sprint_test_controller.sprint_test_dao.get_by_id.return_value = mock_sprint_test

    result = sprint_test_controller.update_test(db=mock_db, test_id=1)

    assert result is mock_sprint_test
    sprint_test_controller.sprint_test_dao.update.assert_not_called()
