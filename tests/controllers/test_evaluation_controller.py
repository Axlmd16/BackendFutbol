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


# ==============================================
# TESTS: SPRINT TEST
# ==============================================


def test_add_sprint_test_success(
    evaluation_controller, mock_db, mock_evaluation, mock_sprint_test
):
    """Agregar Sprint Test exitosamente."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    evaluation_controller.athlete_dao.get_by_id.return_value = Mock()
    evaluation_controller.test_dao.create_sprint_test.return_value = mock_sprint_test

    result = evaluation_controller.add_sprint_test(
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
    evaluation_controller.test_dao.create_sprint_test.assert_called_once()


def test_add_sprint_test_evaluation_not_found(evaluation_controller, mock_db):
    """Agregar Sprint Test a evaluación inexistente."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = None

    # El controlador usa un método estático para validar, entonces mockear la validación
    from unittest.mock import patch

    with patch.object(
        evaluation_controller,
        "_validate_evaluation_exists",
        side_effect=DatabaseException("Evaluación 999 no existe"),
    ):
        with pytest.raises(DatabaseException):
            evaluation_controller.add_sprint_test(
                db=mock_db,
                evaluation_id=999,
                athlete_id=5,
                date=datetime.now(),
                distance_meters=30,
                time_0_10_s=1.85,
                time_0_30_s=3.95,
            )


def test_add_sprint_test_athlete_not_found(
    evaluation_controller, mock_db, mock_evaluation
):
    """Agregar Sprint Test a atleta inexistente."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    evaluation_controller.athlete_dao.get_by_id.return_value = None

    # El controlador usa un método estático para validar, entonces mockear la validación
    from unittest.mock import patch

    with patch.object(
        evaluation_controller,
        "_validate_athlete_exists",
        side_effect=DatabaseException("Atleta 999 no existe"),
    ):
        with pytest.raises(DatabaseException):
            evaluation_controller.add_sprint_test(
                db=mock_db,
                evaluation_id=1,
                athlete_id=999,
                date=datetime.now(),
                distance_meters=30,
                time_0_10_s=1.85,
                time_0_30_s=3.95,
            )


# ==============================================
# TESTS: YOYO TEST
# ==============================================


def test_add_yoyo_test_success(
    evaluation_controller, mock_db, mock_evaluation, mock_yoyo_test
):
    """Agregar Yoyo Test exitosamente."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    evaluation_controller.athlete_dao.get_by_id.return_value = Mock()
    evaluation_controller.test_dao.create_yoyo_test.return_value = mock_yoyo_test

    result = evaluation_controller.add_yoyo_test(
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
    evaluation_controller.test_dao.create_yoyo_test.assert_called_once()


# ==============================================
# TESTS: ENDURANCE TEST
# ==============================================


def test_add_endurance_test_success(
    evaluation_controller, mock_db, mock_evaluation, mock_endurance_test
):
    """Agregar Endurance Test exitosamente."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    evaluation_controller.athlete_dao.get_by_id.return_value = Mock()
    evaluation_controller.test_dao.create_endurance_test.return_value = (
        mock_endurance_test
    )

    result = evaluation_controller.add_endurance_test(
        db=mock_db,
        evaluation_id=1,
        athlete_id=5,
        date=mock_endurance_test.date,
        min_duration=12,
        total_distance_m=2500,
        observations="Cooper test",
    )

    assert result.id == 3
    assert result.type == "endurance_test"
    evaluation_controller.test_dao.create_endurance_test.assert_called_once()


# ==============================================
# TESTS: TECHNICAL ASSESSMENT
# ==============================================


def test_add_technical_assessment_success(
    evaluation_controller, mock_db, mock_evaluation, mock_technical_assessment
):
    """Agregar Technical Assessment exitosamente."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    evaluation_controller.athlete_dao.get_by_id.return_value = Mock()
    evaluation_controller.test_dao.create_technical_assessment.return_value = (
        mock_technical_assessment
    )

    result = evaluation_controller.add_technical_assessment(
        db=mock_db,
        evaluation_id=1,
        athlete_id=5,
        date=mock_technical_assessment.date,
        ball_control="MUY_ALTO",
        short_pass="ALTO",
        long_pass="MEDIO",
        shooting="ALTO",
        dribbling="MUY_ALTO",
        observations="Excellent technical skills",
    )

    assert result.id == 4
    assert result.type == "technical_assessment"
    evaluation_controller.test_dao.create_technical_assessment.assert_called_once()


# ==============================================
# TESTS: TEST MANAGEMENT
# ==============================================


def test_list_tests_by_evaluation_success(
    evaluation_controller, mock_db, mock_evaluation, mock_sprint_test
):
    """Listar tests de una evaluación."""
    evaluation_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    evaluation_controller.test_dao.list_by_evaluation.return_value = [mock_sprint_test]

    result = evaluation_controller.list_tests_by_evaluation(mock_db, 1)

    assert len(result) == 1
    assert result[0].type == "sprint_test"
    evaluation_controller.test_dao.list_by_evaluation.assert_called_once()


def test_delete_test_success(evaluation_controller, mock_db):
    """Eliminar un test."""
    evaluation_controller.test_dao.delete.return_value = True

    result = evaluation_controller.delete_test(mock_db, 1)

    assert result is True
    evaluation_controller.test_dao.delete.assert_called_once_with(mock_db, 1)


def test_delete_test_not_found(evaluation_controller, mock_db):
    """Eliminar test que no existe."""
    evaluation_controller.test_dao.delete.return_value = False

    result = evaluation_controller.delete_test(mock_db, 999)

    assert result is False
