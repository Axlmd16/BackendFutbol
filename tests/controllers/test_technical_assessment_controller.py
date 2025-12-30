"""Tests unitarios para `TechnicalAssessmentController`."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.controllers.technical_assessment_controller import (
    TechnicalAssessmentController,
)
from app.models.evaluation import Evaluation
from app.models.technical_assessment import TechnicalAssessment
from app.utils.exceptions import DatabaseException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def technical_assessment_controller():
    """Fixture para TechnicalAssessmentController con DAOs mockeados."""
    controller = TechnicalAssessmentController()
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

    result = technical_assessment_controller.add_test(
        db=mock_db,
        evaluation_id=1,
        athlete_id=5,
        date=mock_technical_assessment.date,
        ball_control=8,
        short_pass=9,
        long_pass=7,
        shooting=8,
        dribbling=9,
        observations="Excellent technical skills",
    )

    assert result.id == 4
    assert result.type == "technical_assessment"
    assert result.ball_control == 8
    assert result.short_pass == 9
    assert result.long_pass == 7
    assert result.shooting == 8
    assert result.dribbling == 9
    technical_assessment_controller.test_dao.create_technical_assessment.assert_called_once()


def test_add_technical_assessment_evaluation_not_found(
    technical_assessment_controller, mock_db
):
    """Agregar Technical Assessment a evaluación inexistente."""
    technical_assessment_controller.evaluation_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        technical_assessment_controller.add_test(
            db=mock_db,
            evaluation_id=999,
            athlete_id=5,
            date=datetime.now(),
            ball_control=8,
            short_pass=9,
            long_pass=7,
            shooting=8,
            dribbling=9,
        )


def test_add_technical_assessment_athlete_not_found(
    technical_assessment_controller, mock_db, mock_evaluation
):
    """Agregar Technical Assessment a atleta inexistente."""
    technical_assessment_controller.evaluation_dao.get_by_id.return_value = (
        mock_evaluation
    )
    technical_assessment_controller.athlete_dao.get_by_id.return_value = None

    with pytest.raises(DatabaseException, match="Atleta 999 no existe"):
        technical_assessment_controller.add_test(
            db=mock_db,
            evaluation_id=1,
            athlete_id=999,
            date=datetime.now(),
            ball_control=8,
            short_pass=9,
            long_pass=7,
            shooting=8,
            dribbling=9,
        )
