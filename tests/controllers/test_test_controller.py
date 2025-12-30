"""Tests unitarios para `TestController`."""

from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.test_controller import TestController
from app.models.evaluation import Evaluation
from app.models.test import Test
from app.utils.exceptions import DatabaseException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def test_controller():
    """Fixture para TestController con DAOs mockeados."""
    controller = TestController()
    controller.test_dao = MagicMock()
    controller.evaluation_dao = MagicMock()
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
def mock_tests():
    """Fixture de lista de tests mock."""
    test1 = Mock(spec=Test)
    test1.id = 1
    test1.type = "sprint_test"
    test1.athlete_id = 5
    test1.evaluation_id = 1

    test2 = Mock(spec=Test)
    test2.id = 2
    test2.type = "yoyo_test"
    test2.athlete_id = 5
    test2.evaluation_id = 1

    return [test1, test2]


# ==============================================
# TESTS: LIST TESTS BY EVALUATION
# ==============================================


def test_list_tests_by_evaluation_success(
    test_controller, mock_db, mock_evaluation, mock_tests
):
    """Listar tests de una evaluación exitosamente."""
    test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    test_controller.test_dao.list_by_evaluation.return_value = mock_tests

    result = test_controller.list_tests_by_evaluation(db=mock_db, evaluation_id=1)

    assert len(result) == 2
    assert result[0].type == "sprint_test"
    assert result[1].type == "yoyo_test"
    test_controller.test_dao.list_by_evaluation.assert_called_once()


def test_list_tests_by_evaluation_not_found(test_controller, mock_db):
    """Listar tests de evaluación inexistente."""
    test_controller.evaluation_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        test_controller.list_tests_by_evaluation(db=mock_db, evaluation_id=999)


def test_list_tests_by_evaluation_empty(test_controller, mock_db, mock_evaluation):
    """Listar tests cuando no hay tests en la evaluación."""
    test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    test_controller.test_dao.list_by_evaluation.return_value = []

    result = test_controller.list_tests_by_evaluation(db=mock_db, evaluation_id=1)

    assert result == []
    test_controller.test_dao.list_by_evaluation.assert_called_once()


# ==============================================
# TESTS: DELETE TEST
# ==============================================


def test_delete_test_success(test_controller, mock_db):
    """Eliminar test exitosamente."""
    test_controller.test_dao.delete.return_value = True

    result = test_controller.delete_test(db=mock_db, test_id=1)

    assert result is True
    test_controller.test_dao.delete.assert_called_once()


def test_delete_test_not_found(test_controller, mock_db):
    """Eliminar test inexistente."""
    test_controller.test_dao.delete.return_value = False

    result = test_controller.delete_test(db=mock_db, test_id=999)

    assert result is False
