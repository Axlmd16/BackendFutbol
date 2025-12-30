"""Tests unitarios para `YoyoTestController`."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.yoyo_test_controller import YoyoTestController
from app.models.evaluation import Evaluation
from app.models.yoyo_test import YoyoTest
from app.utils.exceptions import DatabaseException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def yoyo_test_controller():
    """Fixture para YoyoTestController con DAOs mockeados."""
    controller = YoyoTestController()
    controller.yoyo_test_dao = MagicMock()
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
def mock_yoyo_test():
    """Fixture de un Yoyo Test mock."""
    test = Mock(spec=YoyoTest)
    test.id = 2
    test.type = "yoyo_test"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.shuttle_count = 47
    test.final_level = "18.2"
    test.failures = 2
    test.observations = "Excellent aerobic capacity"
    test.is_active = True
    return test


# ==============================================
# TESTS: ADD YOYO TEST
# ==============================================


def test_add_yoyo_test_success(
    yoyo_test_controller, mock_db, mock_evaluation, mock_athlete, mock_yoyo_test
):
    """Agregar Yoyo Test exitosamente."""
    yoyo_test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    yoyo_test_controller.athlete_dao.get_by_id.return_value = mock_athlete
    yoyo_test_controller.test_dao.create_yoyo_test.return_value = mock_yoyo_test

    result = yoyo_test_controller.add_test(
        db=mock_db,
        evaluation_id=1,
        athlete_id=5,
        date=mock_yoyo_test.date,
        shuttle_count=47,
        final_level="18.2",
        failures=2,
        observations="Excellent aerobic capacity",
    )

    assert result.id == 2
    assert result.type == "yoyo_test"
    assert result.shuttle_count == 47
    yoyo_test_controller.test_dao.create_yoyo_test.assert_called_once()


def test_add_yoyo_test_evaluation_not_found(yoyo_test_controller, mock_db):
    """Agregar Yoyo Test a evaluación inexistente."""
    yoyo_test_controller.evaluation_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        yoyo_test_controller.add_test(
            db=mock_db,
            evaluation_id=999,
            athlete_id=5,
            date=datetime.now(),
            shuttle_count=47,
            final_level="18.2",
            failures=2,
        )


def test_add_yoyo_test_athlete_not_found(
    yoyo_test_controller, mock_db, mock_evaluation
):
    """Agregar Yoyo Test a atleta inexistente."""
    yoyo_test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    yoyo_test_controller.athlete_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Atleta 999 no existe"):
        yoyo_test_controller.add_test(
            db=mock_db,
            evaluation_id=1,
            athlete_id=999,
            date=datetime.now(),
            shuttle_count=47,
            final_level="18.2",
            failures=2,
        )


# ==============================================
# TESTS: UPDATE YOYO TEST
# ==============================================


def test_update_yoyo_test_success(yoyo_test_controller, mock_db, mock_yoyo_test):
    """Actualizar campos de un Yoyo Test existente."""
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = mock_yoyo_test
    updated = Mock()
    updated.id = mock_yoyo_test.id
    updated.shuttle_count = 55
    yoyo_test_controller.yoyo_test_dao.update.return_value = updated

    result = yoyo_test_controller.update_test(
        db=mock_db, test_id=2, shuttle_count=55, observations="Mejoró"
    )

    assert result.shuttle_count == 55
    yoyo_test_controller.yoyo_test_dao.update.assert_called_once_with(
        mock_db, 2, {"shuttle_count": 55, "observations": "Mejoró"}
    )


def test_update_yoyo_test_not_found(yoyo_test_controller, mock_db):
    """Retorna None si el Yoyo Test no existe."""
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = None

    result = yoyo_test_controller.update_test(db=mock_db, test_id=999)

    assert result is None
    yoyo_test_controller.yoyo_test_dao.update.assert_not_called()


def test_update_yoyo_test_evaluation_not_found(yoyo_test_controller, mock_db):
    """Valida evaluación al actualizar."""
    yoyo_test_controller.evaluation_dao.get_by_id.return_value = None
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = Mock()

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        yoyo_test_controller.update_test(
            db=mock_db, test_id=2, evaluation_id=999, shuttle_count=50
        )


def test_update_yoyo_test_athlete_not_found(yoyo_test_controller, mock_db):
    """Valida atleta al actualizar."""
    yoyo_test_controller.evaluation_dao.get_by_id.return_value = Mock()
    yoyo_test_controller.athlete_dao.get_by_id.return_value = None
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = Mock()

    with pytest.raises(DatabaseException, match="Atleta 888 no existe"):
        yoyo_test_controller.update_test(
            db=mock_db, test_id=2, athlete_id=888, shuttle_count=50
        )


def test_update_yoyo_test_no_fields_returns_existing(
    yoyo_test_controller, mock_db, mock_yoyo_test
):
    """Si no se envían campos, devuelve la instancia actual."""
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = mock_yoyo_test

    result = yoyo_test_controller.update_test(db=mock_db, test_id=2)

    assert result is mock_yoyo_test
    yoyo_test_controller.yoyo_test_dao.update.assert_not_called()
