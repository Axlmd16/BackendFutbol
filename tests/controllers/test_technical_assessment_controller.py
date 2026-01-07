"""Tests unitarios para `TechnicalAssessmentController`."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.technical_assessment_controller import (
    TechnicalAssessmentController,
)
from app.models.enums.scale import Scale
from app.models.evaluation import Evaluation
from app.models.technical_assessment import TechnicalAssessment
from app.schemas.technical_assessment_schema import (
    CreateTechnicalAssessmentSchema,
    UpdateTechnicalAssessmentSchema,
)

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def technical_assessment_controller():
    """Fixture para TechnicalAssessmentController con DAOs mockeados."""
    controller = TechnicalAssessmentController()
    controller.technical_assessment_dao = MagicMock()
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
def mock_technical_assessment():
    """Fixture de un Technical Assessment mock."""
    test = Mock(spec=TechnicalAssessment)
    test.id = 4
    test.type = "technical_assessment"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.ball_control = 8
    test.short_pass = 9
    test.long_pass = 7
    test.shooting = 8
    test.dribbling = 9
    test.observations = "Excellent technical skills"
    test.is_active = True
    return test


# ==============================================
# TESTS: ADD TECHNICAL ASSESSMENT
# ==============================================


def test_add_technical_assessment_success(
    technical_assessment_controller,
    mock_db,
    mock_evaluation,
    mock_athlete,
    mock_technical_assessment,
):
    """Agregar Technical Assessment exitosamente."""
    technical_assessment_controller.evaluation_dao.get_by_id.return_value = (
        mock_evaluation
    )
    technical_assessment_controller.athlete_dao.get_by_id.return_value = mock_athlete
    technical_assessment_controller.test_dao.create_technical_assessment.return_value = mock_technical_assessment  # noqa: E501

    payload = CreateTechnicalAssessmentSchema(
        evaluation_id=1,
        athlete_id=5,
        date=mock_technical_assessment.date,
        ball_control=Scale.EXCELLENT,
        short_pass=Scale.EXCELLENT,
        long_pass=Scale.GOOD,
        shooting=Scale.GOOD,
        dribbling=Scale.EXCELLENT,
        observations="Excellent technical skills",
    )

    result = technical_assessment_controller.add_test(
        db=mock_db,
        payload=payload,
    )

    assert result.id == 4
    assert result.type == "technical_assessment"
    assert result.ball_control == 8
    assert result.short_pass == 9
    assert result.long_pass == 7
    assert result.shooting == 8
    assert result.dribbling == 9
    technical_assessment_controller.test_dao.create_technical_assessment.assert_called_once()


# ==============================================
# TESTS: UPDATE TECHNICAL ASSESSMENT
# ==============================================


def test_update_technical_assessment_success(
    technical_assessment_controller, mock_db, mock_technical_assessment
):
    """Actualizar campos de un Technical Assessment existente."""
    technical_assessment_controller.technical_assessment_dao.get_by_id.return_value = (
        mock_technical_assessment
    )
    updated = Mock()
    updated.id = mock_technical_assessment.id
    updated.ball_control = "Excellent"
    technical_assessment_controller.technical_assessment_dao.update.return_value = (
        updated
    )

    payload = UpdateTechnicalAssessmentSchema(
        ball_control=Scale.EXCELLENT,
        observations="Mejoró",
    )

    result = technical_assessment_controller.update_test(
        db=mock_db,
        test_id=4,
        payload=payload,
    )

    assert result.ball_control == "Excellent"
    technical_assessment_controller.technical_assessment_dao.update.assert_called_once_with(
        mock_db,
        4,
        {"ball_control": Scale.EXCELLENT, "observations": "Mejoró"},
    )


# ==============================================
# TESTS: DELETE TECHNICAL ASSESSMENT
# ==============================================


def test_delete_technical_assessment_success(
    technical_assessment_controller, mock_db, mock_technical_assessment
):
    """Elimina cuando existe."""
    technical_assessment_controller.technical_assessment_dao.get_by_id.return_value = (
        mock_technical_assessment
    )
    technical_assessment_controller.technical_assessment_dao.delete.return_value = None

    result = technical_assessment_controller.delete_test(mock_db, test_id=4)

    assert result is True
    technical_assessment_controller.technical_assessment_dao.delete.assert_called_once_with(
        mock_db, 4
    )


def test_update_technical_assessment_no_fields_returns_existing(
    technical_assessment_controller, mock_db, mock_technical_assessment
):
    """Sin campos a actualizar devuelve la entidad actual."""
    technical_assessment_controller.technical_assessment_dao.get_by_id.return_value = (
        mock_technical_assessment
    )

    payload = UpdateTechnicalAssessmentSchema()

    result = technical_assessment_controller.update_test(
        db=mock_db,
        test_id=4,
        payload=payload,
    )

    assert result is mock_technical_assessment
    technical_assessment_controller.technical_assessment_dao.update.assert_not_called()
