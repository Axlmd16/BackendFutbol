"""Tests unitarios para `SprintTestController`."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.sprint_test_controller import SprintTestController
from app.models.evaluation import Evaluation
from app.models.sprint_test import SprintTest
from app.schemas.sprint_test_schema import (
    CreateSprintTestSchema,
    UpdateSprintTestSchema,
)

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

    payload = CreateSprintTestSchema(
        evaluation_id=1,
        athlete_id=5,
        date=mock_sprint_test.date,
        distance_meters=30,
        time_0_10_s=1.85,
        time_0_30_s=3.95,
        observations="Good performance",
    )

    result = sprint_test_controller.add_test(
        db=mock_db,
        payload=payload,
    )

    assert result.id == 1
    assert result.type == "sprint_test"
    assert result.distance_meters == 30
    sprint_test_controller.test_dao.create_sprint_test.assert_called_once()


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

    payload = UpdateSprintTestSchema(
        time_0_30_s=3.80,
        observations="Mejoró salida",
    )

    result = sprint_test_controller.update_test(
        db=mock_db,
        test_id=1,
        payload=payload,
    )

    assert result.time_0_30_s == 3.80
    sprint_test_controller.sprint_test_dao.update.assert_called_once_with(
        mock_db, 1, {"time_0_30_s": 3.80, "observations": "Mejoró salida"}
    )


def test_update_sprint_test_no_fields_returns_existing(
    sprint_test_controller, mock_db, mock_sprint_test
):
    """Si no se envían campos, se retorna la instancia actual."""
    sprint_test_controller.sprint_test_dao.get_by_id.return_value = mock_sprint_test

    payload = UpdateSprintTestSchema()

    result = sprint_test_controller.update_test(
        db=mock_db,
        test_id=1,
        payload=payload,
    )

    assert result is mock_sprint_test
    sprint_test_controller.sprint_test_dao.update.assert_not_called()


# ==============================================
# TESTS: DELETE SPRINT TEST
# ==============================================


def test_delete_sprint_test_success(
    monkeypatch, sprint_test_controller, mock_db, mock_sprint_test
):
    """Elimina y actualiza estadísticas cuando existe."""
    sprint_test_controller.sprint_test_dao.get_by_id.return_value = mock_sprint_test
    sprint_test_controller.sprint_test_dao.delete.return_value = None

    called = {"stats": False}

    def _update_stats(db, athlete_id):
        called["stats"] = True
        assert athlete_id == mock_sprint_test.athlete_id

    monkeypatch.setattr(
        "app.controllers.sprint_test_controller.statistic_controller.update_athlete_stats",
        _update_stats,
    )

    result = sprint_test_controller.delete_test(mock_db, test_id=1)

    assert result is True
    sprint_test_controller.sprint_test_dao.delete.assert_called_once_with(mock_db, 1)
    assert called["stats"] is True
