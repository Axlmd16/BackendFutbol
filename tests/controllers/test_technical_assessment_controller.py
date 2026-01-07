"""Tests unitarios para `TechnicalAssessmentController`."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

import pytest
from pydantic import ValidationError

from app.controllers.technical_assessment_controller import (
    TechnicalAssessmentController,
)
from app.models.enums.scale import Scale
from app.models.evaluation import Evaluation
from app.models.technical_assessment import TechnicalAssessment
from app.schemas.technical_assessment_schema import (
    CreateTechnicalAssessmentSchema,
)
from app.utils.exceptions import DatabaseException

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

    result = technical_assessment_controller.update_test(
        db=mock_db, test_id=4, ball_control="Excellent", observations="Mejoró"
    )

    assert result.ball_control == "Excellent"
    technical_assessment_controller.technical_assessment_dao.update.assert_called_once_with(
        mock_db, 4, {"ball_control": "Excellent", "observations": "Mejoró"}
    )


def test_update_technical_assessment_not_found(
    technical_assessment_controller, mock_db
):
    """Retorna None si el Technical Assessment no existe."""
    technical_assessment_controller.technical_assessment_dao.get_by_id.return_value = (
        None
    )

    result = technical_assessment_controller.update_test(db=mock_db, test_id=999)

    assert result is None
    technical_assessment_controller.technical_assessment_dao.update.assert_not_called()


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


def test_delete_technical_assessment_not_found(
    technical_assessment_controller, mock_db
):
    """Si no existe retorna False y no borra."""
    technical_assessment_controller.technical_assessment_dao.get_by_id.return_value = (
        None
    )

    result = technical_assessment_controller.delete_test(mock_db, test_id=999)

    assert result is False
    technical_assessment_controller.technical_assessment_dao.delete.assert_not_called()


def test_update_technical_assessment_evaluation_not_found(
    technical_assessment_controller, mock_db
):
    """Valida evaluación al actualizar."""
    technical_assessment_controller.evaluation_dao.get_by_id.return_value = None
    technical_assessment_controller.technical_assessment_dao.get_by_id.return_value = (
        Mock()
    )

    with pytest.raises(DatabaseException, match="Evaluación 999 no existe"):
        technical_assessment_controller.update_test(
            db=mock_db, test_id=4, evaluation_id=999, shooting="Good"
        )


def test_update_technical_assessment_athlete_not_found(
    technical_assessment_controller, mock_db
):
    """Valida atleta al actualizar."""
    technical_assessment_controller.evaluation_dao.get_by_id.return_value = Mock()
    technical_assessment_controller.athlete_dao.get_by_id.return_value = None
    technical_assessment_controller.technical_assessment_dao.get_by_id.return_value = (
        Mock()
    )

    with pytest.raises(DatabaseException, match="Atleta 888 no existe"):
        technical_assessment_controller.update_test(
            db=mock_db, test_id=4, athlete_id=888, shooting="Good"
        )


def test_update_technical_assessment_no_fields_returns_existing(
    technical_assessment_controller, mock_db, mock_technical_assessment
):
    """Sin campos a actualizar devuelve la entidad actual."""
    technical_assessment_controller.technical_assessment_dao.get_by_id.return_value = (
        mock_technical_assessment
    )

    result = technical_assessment_controller.update_test(db=mock_db, test_id=4)

    assert result is mock_technical_assessment
    technical_assessment_controller.technical_assessment_dao.update.assert_not_called()


# ==============================================
# TESTS: LIST TECHNICAL ASSESSMENTS
# ==============================================


def test_list_tests_success(
    technical_assessment_controller, mock_db, mock_technical_assessment
):
    """Lista technical assessments con paginación y filtros."""
    from app.schemas.technical_assessment_schema import TechnicalAssessmentFilter

    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_with_entities = MagicMock()
    mock_order = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.with_entities.return_value = mock_with_entities
    mock_with_entities.scalar.return_value = 4
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = [mock_technical_assessment]

    filters = TechnicalAssessmentFilter(page=1, limit=10)
    items, total = technical_assessment_controller.list_tests(mock_db, filters)

    assert len(items) == 1
    assert total == 4
    assert items[0] is mock_technical_assessment


def test_list_tests_with_filters(technical_assessment_controller, mock_db):
    """Lista technical assessments filtrando por evaluation_id y athlete_id."""
    from app.schemas.technical_assessment_schema import TechnicalAssessmentFilter

    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_with_entities = MagicMock()
    mock_order = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.with_entities.return_value = mock_with_entities
    mock_with_entities.scalar.return_value = 2
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = []

    filters = TechnicalAssessmentFilter(page=1, limit=10, evaluation_id=1, athlete_id=5)
    items, total = technical_assessment_controller.list_tests(mock_db, filters)

    assert items == []
    assert total == 2


def test_list_tests_with_search(
    technical_assessment_controller, mock_db, mock_technical_assessment
):
    """Lista technical assessments filtrando por nombre de atleta (search)."""
    from app.schemas.technical_assessment_schema import TechnicalAssessmentFilter

    mock_query = MagicMock()
    mock_join = MagicMock()
    mock_filter = MagicMock()
    mock_with_entities = MagicMock()
    mock_order = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.join.return_value = mock_join
    mock_join.filter.return_value = mock_filter
    mock_filter.with_entities.return_value = mock_with_entities
    mock_with_entities.scalar.return_value = 1
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = [mock_technical_assessment]

    filters = TechnicalAssessmentFilter(page=1, limit=10, search="María")
    items, total = technical_assessment_controller.list_tests(mock_db, filters)

    assert len(items) == 1
    assert total == 1


def test_list_tests_with_search_no_match(technical_assessment_controller, mock_db):
    """Lista technical assessments con search que no coincide devuelve lista vacía."""
    from app.schemas.technical_assessment_schema import TechnicalAssessmentFilter

    mock_query = MagicMock()
    mock_join = MagicMock()
    mock_filter = MagicMock()
    mock_with_entities = MagicMock()
    mock_order = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.join.return_value = mock_join
    mock_join.filter.return_value = mock_filter
    mock_filter.with_entities.return_value = mock_with_entities
    mock_with_entities.scalar.return_value = 0
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = []

    filters = TechnicalAssessmentFilter(page=1, limit=10, search="NoExiste")
    items, total = technical_assessment_controller.list_tests(mock_db, filters)

    assert items == []
    assert total == 0


# ==============================================
# TESTS: VALIDACIONES
# ==============================================


def test_technical_assessment_future_date_rejected():
    """Validación: La fecha del test no puede ser futura."""
    future_date = datetime.now() + timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        CreateTechnicalAssessmentSchema(
            date=future_date,
            athlete_id=1,
            evaluation_id=1,
            ball_control=Scale.GOOD,
        )

    assert "La fecha del test no puede ser futura" in str(exc_info.value)


def test_technical_assessment_all_skills_none_rejected():
    """Validación: Rechaza evaluación sin ninguna habilidad."""
    with pytest.raises(ValidationError) as exc_info:
        CreateTechnicalAssessmentSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            ball_control=None,
            short_pass=None,
            long_pass=None,
            shooting=None,
            dribbling=None,
        )

    assert "Debe evaluar al menos una habilidad técnica" in str(exc_info.value)


def test_technical_assessment_one_skill_valid():
    """Validación: Válido con solo una habilidad."""
    schema = CreateTechnicalAssessmentSchema(
        date=datetime.now(),
        athlete_id=1,
        evaluation_id=1,
        ball_control=Scale.GOOD,
    )

    assert schema.ball_control == Scale.GOOD
    assert schema.short_pass is None


def test_technical_assessment_multiple_skills_valid():
    """Validación: Válido con múltiples habilidades."""
    schema = CreateTechnicalAssessmentSchema(
        date=datetime.now(),
        athlete_id=1,
        evaluation_id=1,
        ball_control=Scale.GOOD,
        short_pass=Scale.EXCELLENT,
        shooting=Scale.AVERAGE,
    )

    assert schema.ball_control == Scale.GOOD
    assert schema.short_pass == Scale.EXCELLENT
    assert schema.shooting == Scale.AVERAGE


def test_technical_assessment_all_skills_valid():
    """Validación: Válido con todas las habilidades evaluadas."""
    schema = CreateTechnicalAssessmentSchema(
        date=datetime.now(),
        athlete_id=1,
        evaluation_id=1,
        ball_control=Scale.GOOD,
        short_pass=Scale.EXCELLENT,
        long_pass=Scale.AVERAGE,
        shooting=Scale.GOOD,
        dribbling=Scale.EXCELLENT,
    )

    assert schema.ball_control == Scale.GOOD
    assert schema.short_pass == Scale.EXCELLENT
    assert schema.long_pass == Scale.AVERAGE
    assert schema.shooting == Scale.GOOD
    assert schema.dribbling == Scale.EXCELLENT
