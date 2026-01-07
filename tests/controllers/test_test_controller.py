"""Tests unitarios para `TestController`."""

from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.test_controller import TestController
from app.models.evaluation import Evaluation
from app.models.test import Test

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
