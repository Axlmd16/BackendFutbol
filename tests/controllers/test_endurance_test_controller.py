"""Tests unitarios para `EnduranceTestController`."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.endurance_test_controller import EnduranceTestController
from app.models.endurance_test import EnduranceTest
from app.models.evaluation import Evaluation

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


# ==============================================
# TESTS: DELETE ENDURANCE TEST
# ==============================================


def test_delete_endurance_test_success(
    monkeypatch, endurance_test_controller, mock_db, mock_endurance_test
):
    """Elimina y actualiza estadísticas cuando existe."""
    endurance_test_controller.endurance_test_dao.get_by_id.return_value = (
        mock_endurance_test
    )
    endurance_test_controller.endurance_test_dao.delete.return_value = None

    called = {"stats": False}

    def _update_stats(db, athlete_id):
        called["stats"] = True
        assert athlete_id == mock_endurance_test.athlete_id

    monkeypatch.setattr(
        "app.controllers.endurance_test_controller.statistic_controller.update_athlete_stats",
        _update_stats,
    )

    result = endurance_test_controller.delete_test(mock_db, test_id=3)

    assert result is True
    endurance_test_controller.endurance_test_dao.delete.assert_called_once_with(
        mock_db, 3
    )
    assert called["stats"] is True
