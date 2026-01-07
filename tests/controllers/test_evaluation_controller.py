"""Tests unitarios para `EvaluationController`."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

import pytest
from pydantic import ValidationError

from app.controllers.evaluation_controller import EvaluationController
from app.models.endurance_test import EnduranceTest
from app.models.evaluation import Evaluation
from app.models.sprint_test import SprintTest
from app.models.technical_assessment import TechnicalAssessment
from app.models.yoyo_test import YoyoTest
from app.schemas.evaluation_schema import (
    CreateEvaluationSchema,
    UpdateEvaluationSchema,
)
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

    payload = CreateEvaluationSchema(
        name="Evaluación Física",
        date="2026-06-01",
        time="10:59",
        user_id=1,
        location="Cancha Principal",
        observations="Test inicial",
    )

    result = evaluation_controller.create_evaluation(
        db=mock_db,
        payload=payload,
    )

    assert result.id == 1
    assert result.name == "Evaluación Física"
    evaluation_controller.evaluation_dao.create.assert_called_once()


def test_create_evaluation_date_validation_error(evaluation_controller, mock_db):
    """Crear evaluación con validación fallida."""
    evaluation_controller.evaluation_dao.create.side_effect = DatabaseException(
        "La fecha de evaluación no puede ser anterior a hoy"
    )

    payload = CreateEvaluationSchema(
        name="Evaluación Pasada",
        date="2020-01-01",
        time="10:30",
        user_id=1,
        location="Cancha Principal",
        observations="Test pasado",
    )

    with pytest.raises(DatabaseException):
        evaluation_controller.create_evaluation(
            db=mock_db,
            payload=payload,
        )


def test_create_evaluation_invalid_date():
    """Debe rechazar payload con fecha en formato inválido."""
    with pytest.raises(ValidationError) as exc_info:
        CreateEvaluationSchema(
            name="Evaluación Fecha Inválida",
            date="fecha-invalida",
            time="10:30",
            user_id=1,
            location="Cancha Principal",
            observations="Formato incorrecto",
        )
    assert "Input should be a valid datetime" in str(exc_info.value)


def test_create_evaluation_invalid_time():
    """Debe rechazar payload con hora fuera del formato HH:MM."""
    with pytest.raises(ValidationError) as exc_info:
        CreateEvaluationSchema(
            name="Evaluación Hora Inválida",
            date="2026-06-01",
            time="25:99",
            user_id=1,
            location="Cancha Principal",
            observations="Hora inválida",
        )
    assert "hora de evaluación es inválida" in str(exc_info.value).lower()


def test_create_evaluation_name_too_short():
    """Debe rechazar payload con nombre menor al mínimo permitido."""
    with pytest.raises(ValidationError) as exc_info:
        CreateEvaluationSchema(
            name="AB",
            date="2026-06-01",
            time="10:30",
            user_id=1,
            location="Cancha Principal",
            observations="Nombre demasiado corto",
        )
    assert "El nombre de la evaluación debe tener al menos 3 caracteres" in str(
        exc_info.value
    )


def test_update_evaluation_success(evaluation_controller, mock_db, mock_evaluation):
    """Actualizar una evaluación exitosamente."""
    updated_eval = Mock(spec=Evaluation)
    updated_eval.id = 1
    updated_eval.name = "Evaluación Actualizada"
    updated_eval.date = mock_evaluation.date
    updated_eval.time = "11:00"
    updated_eval.location = "Cancha Auxiliarsss"
    updated_eval.observations = "Updated"

    evaluation_controller.evaluation_dao.update.return_value = updated_eval

    payload = UpdateEvaluationSchema(
        name="Evaluación Actualizada",
        date=mock_evaluation.date,
        time="11:59",
        location="Cancha Auxiliar",
    )

    result = evaluation_controller.update_evaluation(
        db=mock_db,
        evaluation_id=1,
        payload=payload,
    )

    assert result.name == "Evaluación Actualizada"
    evaluation_controller.evaluation_dao.update.assert_called_once()


def test_update_evaluation_invalid_date(evaluation_controller, mock_db):
    """Rechaza fecha inválida al actualizar."""
    payload = UpdateEvaluationSchema(name="Eval", date=datetime.now())
    payload.date = "3asdasdsad"  # type: ignore[assignment]
    with pytest.raises(DatabaseException, match="fecha de evaluación es inválida"):
        evaluation_controller.update_evaluation(
            db=mock_db,
            evaluation_id=1,
            payload=payload,
        )
    evaluation_controller.evaluation_dao.update.assert_not_called()


def test_update_evaluation_invalid_time(
    evaluation_controller, mock_db, mock_evaluation
):
    """Rechaza hora inválida al actualizar."""
    payload = UpdateEvaluationSchema(date=mock_evaluation.date, time="10:50")
    payload.time = "asdasdsa"  # type: ignore[assignment]
    with pytest.raises(DatabaseException, match="hora de evaluación es inválida"):
        evaluation_controller.update_evaluation(
            db=mock_db,
            evaluation_id=1,
            payload=payload,
        )
    evaluation_controller.evaluation_dao.update.assert_not_called()


def test_delete_evaluation_success(evaluation_controller, mock_db):
    """Eliminar una evaluación existente."""
    evaluation_controller.evaluation_dao.delete.return_value = True

    result = evaluation_controller.delete_evaluation(mock_db, 1)

    assert result is True
    evaluation_controller.evaluation_dao.delete.assert_called_once_with(mock_db, 1)


# Nota: Tests para test_management (add_sprint_test, add_yoyo_test, etc.)
# han sido movidos a sus controladores específicos:
# - sprint_test_controller
# - yoyo_test_controller
# - endurance_test_controller
# - technical_assessment_controller
# - test_controller
