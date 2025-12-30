"""Tests unitarios para `EvaluationController`."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.evaluation_controller import EvaluationController
from app.models.endurance_test import EnduranceTest
from app.models.evaluation import Evaluation
from app.models.sprint_test import SprintTest
from app.models.technical_assessment import TechnicalAssessment
from app.models.yoyo_test import YoyoTest
from app.utils.exceptions import DatabaseException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def evaluation_controller():
    """Fixture para EvaluationController con DAOs mockeados."""
    controller = EvaluationController()
    controller.evaluation_dao = MagicMock()
    controller.test_dao = MagicMock()
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
    evaluation.date = datetime.now() + timedelta(days=1)
    evaluation.time = "10:30"
    evaluation.location = "Cancha Principal"
    evaluation.observations = "Test initial"
    evaluation.user_id = 1
    evaluation.is_active = True
    evaluation.created_at = datetime.now()
    evaluation.updated_at = None
    evaluation.tests = []
    return evaluation


@pytest.fixture
def mock_sprint_test():
    """Fixture de un Sprint Test mock."""
    test = Mock(spec=SprintTest)
    test.id = 1
    test.type = "sprint_test"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.observations = "Good performance"
    test.distance_meters = 30
    test.time_0_10_s = 1.85
    test.time_0_30_s = 3.95
    test.is_active = True
    return test


@pytest.fixture
def mock_yoyo_test():
    """Fixture de un Yoyo Test mock."""
    test = Mock(spec=YoyoTest)
    test.id = 2
    test.type = "yoyo_test"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.observations = "Excellent aerobic capacity"
    test.shuttle_count = 47
    test.final_level = "18.2"
    test.failures = 2
    test.is_active = True
    return test


@pytest.fixture
def mock_endurance_test():
    """Fixture de un Endurance Test mock."""
    test = Mock(spec=EnduranceTest)
    test.id = 3
    test.type = "endurance_test"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.observations = "Cooper test"
    test.min_duration = 12
    test.total_distance_m = 2500
    test.is_active = True
    return test


@pytest.fixture
def mock_technical_assessment():
    """Fixture de una Technical Assessment mock."""
    test = Mock(spec=TechnicalAssessment)
    test.id = 4
    test.type = "technical_assessment"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.observations = "Excellent technical skills"
    test.ball_control = "MUY_ALTO"
    test.short_pass = "ALTO"
    test.long_pass = "MEDIO"
    test.shooting = "ALTO"
    test.dribbling = "MUY_ALTO"
    test.is_active = True
    return test


# ==============================================
# TESTS: CRUD EVALUATIONS
# ==============================================


def test_create_evaluation_success(evaluation_controller, mock_db, mock_evaluation):
    """Crear una evaluación exitosamente."""
    evaluation_controller.evaluation_dao.create.return_value = mock_evaluation

    result = evaluation_controller.create_evaluation(
        db=mock_db,
        name="Evaluación Física",
        date=mock_evaluation.date,
        time="10:30",
        user_id=1,
        location="Cancha Principal",
        observations="Test initial",
    )

    assert result.id == 1
    assert result.name == "Evaluación Física"
    evaluation_controller.evaluation_dao.create.assert_called_once()


def test_create_evaluation_validation_error(evaluation_controller, mock_db):
    """Crear evaluación con validación fallida."""
    evaluation_controller.evaluation_dao.create.side_effect = DatabaseException(
        "La fecha de evaluación no puede ser anterior a hoy"
    )

    with pytest.raises(DatabaseException):
        evaluation_controller.create_evaluation(
            db=mock_db,
            name="Evaluación Pasada",
            date=datetime.now() - timedelta(days=1),
            time="10:30",
            user_id=1,
        )


def test_get_evaluation_success(evaluation_controller, mock_db, mock_evaluation):
    """Obtener una evaluación existente."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = mock_evaluation

    result = evaluation_controller.get_evaluation(mock_db, 1)

    assert result.id == 1
    assert result.name == "Evaluación Física"
    evaluation_controller.evaluation_dao.get_by_id.assert_called_once_with(mock_db, 1)


def test_get_evaluation_not_found(evaluation_controller, mock_db):
    """Obtener una evaluación que no existe."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = None

    result = evaluation_controller.get_evaluation(mock_db, 999)

    assert result is None


def test_list_evaluations_success(evaluation_controller, mock_db, mock_evaluation):
    """Listar evaluaciones exitosamente."""
    evaluation_controller.evaluation_dao.list_all.return_value = [mock_evaluation]

    result = evaluation_controller.list_evaluations(mock_db, skip=0, limit=10)

    assert len(result) == 1
    assert result[0].id == 1
    evaluation_controller.evaluation_dao.list_all.assert_called_once_with(
        mock_db, 0, 10
    )


def test_list_evaluations_by_user_success(
    evaluation_controller, mock_db, mock_evaluation
):
    """Listar evaluaciones de un usuario."""
    evaluation_controller.evaluation_dao.list_by_user.return_value = [mock_evaluation]

    result = evaluation_controller.list_evaluations_by_user(mock_db, 1)

    assert len(result) == 1
    evaluation_controller.evaluation_dao.list_by_user.assert_called_once()


def test_update_evaluation_success(evaluation_controller, mock_db, mock_evaluation):
    """Actualizar una evaluación exitosamente."""
    updated_eval = Mock(spec=Evaluation)
    updated_eval.id = 1
    updated_eval.name = "Evaluación Actualizada"
    updated_eval.date = mock_evaluation.date
    updated_eval.time = "11:00"
    updated_eval.location = "Cancha Auxiliar"
    updated_eval.observations = "Updated"

    evaluation_controller.evaluation_dao.update.return_value = updated_eval

    result = evaluation_controller.update_evaluation(
        db=mock_db,
        evaluation_id=1,
        name="Evaluación Actualizada",
        time="11:00",
        location="Cancha Auxiliar",
    )

    assert result.name == "Evaluación Actualizada"
    evaluation_controller.evaluation_dao.update.assert_called_once()


def test_update_evaluation_not_found(evaluation_controller, mock_db):
    """Actualizar evaluación que no existe."""
    evaluation_controller.evaluation_dao.update.return_value = None

    result = evaluation_controller.update_evaluation(
        db=mock_db,
        evaluation_id=999,
        name="Nueva Evaluación",
    )

    assert result is None


def test_delete_evaluation_success(evaluation_controller, mock_db):
    """Eliminar una evaluación existente."""
    evaluation_controller.evaluation_dao.delete.return_value = True

    result = evaluation_controller.delete_evaluation(mock_db, 1)

    assert result is True
    evaluation_controller.evaluation_dao.delete.assert_called_once_with(mock_db, 1)


def test_delete_evaluation_not_found(evaluation_controller, mock_db):
    """Eliminar evaluación que no existe."""
    evaluation_controller.evaluation_dao.delete.return_value = False

    result = evaluation_controller.delete_evaluation(mock_db, 999)

    assert result is False


# Nota: Tests para test_management (add_sprint_test, add_yoyo_test, etc.)
# han sido movidos a sus controladores específicos:
# - sprint_test_controller
# - yoyo_test_controller
# - endurance_test_controller
# - technical_assessment_controller
# - test_controller
