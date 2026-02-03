"""Tests unitarios para `SprintTestController`."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

import pytest
from pydantic import ValidationError

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


def test_delete_sprint_test_not_found(sprint_test_controller, mock_db):
    """Si no existe retorna False y no borra."""
    sprint_test_controller.sprint_test_dao.get_by_id.return_value = None

    result = sprint_test_controller.delete_test(mock_db, test_id=999)

    assert result is False
    sprint_test_controller.sprint_test_dao.delete.assert_not_called()


# ==============================================
# TESTS: LIST SPRINT TESTS
# ==============================================


def test_list_tests_success(sprint_test_controller, mock_db, mock_sprint_test):
    """Lista sprint tests con paginación y filtros."""
    from app.schemas.sprint_test_schema import SprintTestFilter

    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_with_entities = MagicMock()
    mock_order = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.with_entities.return_value = mock_with_entities
    mock_with_entities.scalar.return_value = 3
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = [mock_sprint_test]

    filters = SprintTestFilter(page=1, limit=10)
    items, total = sprint_test_controller.list_tests(mock_db, filters)

    assert len(items) == 1
    assert total == 3
    assert items[0] is mock_sprint_test


def test_list_tests_with_filters(sprint_test_controller, mock_db):
    """Lista sprint tests filtrando por evaluation_id y athlete_id."""
    from app.schemas.sprint_test_schema import SprintTestFilter

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
    mock_with_entities.scalar.return_value = 1
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = []

    filters = SprintTestFilter(page=1, limit=10, evaluation_id=1, athlete_id=5)
    items, total = sprint_test_controller.list_tests(mock_db, filters)

    assert items == []
    assert total == 1


def test_list_tests_with_search(sprint_test_controller, mock_db, mock_sprint_test):
    """Lista sprint tests filtrando por nombre de atleta (search)."""
    from app.schemas.sprint_test_schema import SprintTestFilter

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
    mock_limit.all.return_value = [mock_sprint_test]

    filters = SprintTestFilter(page=1, limit=10, search="Carlos")
    items, total = sprint_test_controller.list_tests(mock_db, filters)

    assert len(items) == 1
    assert total == 1


def test_list_tests_with_search_no_match(sprint_test_controller, mock_db):
    """Lista sprint tests con search que no coincide devuelve lista vacía."""
    from app.schemas.sprint_test_schema import SprintTestFilter

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

    filters = SprintTestFilter(page=1, limit=10, search="NoExiste")
    items, total = sprint_test_controller.list_tests(mock_db, filters)

    assert items == []


# ==============================================
# TESTS: VALIDACIONES
# ==============================================


def test_sprint_test_future_date_rejected():
    """Validación: La fecha del test no puede ser futura."""
    future_date = datetime.now() + timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        CreateSprintTestSchema(
            date=future_date,
            athlete_id=1,
            evaluation_id=1,
            distance_meters=30,
            time_0_10_s=1.85,
            time_0_30_s=3.95,
        )

    assert "La fecha del test no puede ser futura" in str(exc_info.value)


def test_sprint_test_valid_past_date():
    """Validación: Las fechas pasadas son válidas."""
    past_date = datetime.now() - timedelta(days=1)

    schema = CreateSprintTestSchema(
        date=past_date,
        athlete_id=1,
        evaluation_id=1,
        distance_meters=30,
        time_0_10_s=1.85,
        time_0_30_s=3.95,
    )

    assert schema.date == past_date


def test_sprint_test_time_coherence_rejected():
    """Validación: time_0_10_s debe ser menor que time_0_30_s."""
    with pytest.raises(ValidationError) as exc_info:
        CreateSprintTestSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            distance_meters=30,
            time_0_10_s=4.0,
            time_0_30_s=3.5,
        )

    assert "debe ser menor que" in str(exc_info.value)


def test_sprint_test_time_equal_rejected():
    """Validación: Tiempos iguales son rechazados."""
    with pytest.raises(ValidationError) as exc_info:
        CreateSprintTestSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            distance_meters=30,
            time_0_10_s=3.5,
            time_0_30_s=3.5,
        )

    assert "debe ser menor que" in str(exc_info.value)


def test_sprint_test_valid_time_progression():
    """Validación: Progresión de tiempos válida."""
    schema = CreateSprintTestSchema(
        date=datetime.now(),
        athlete_id=1,
        evaluation_id=1,
        distance_meters=30,
        time_0_10_s=1.85,
        time_0_30_s=3.95,
    )

    assert schema.time_0_10_s < schema.time_0_30_s


def test_sprint_test_distance_limit_exceeded():
    """Validación: Distancia máxima 1000m."""
    with pytest.raises(ValidationError) as exc_info:
        CreateSprintTestSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            distance_meters=1500,
            time_0_10_s=1.85,
            time_0_30_s=3.95,
        )

    assert "menor o igual a 1000" in str(exc_info.value)


def test_sprint_test_time_limit_exceeded():
    """Validación: Tiempo máximo 60s."""
    with pytest.raises(ValidationError) as exc_info:
        CreateSprintTestSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            distance_meters=30,
            time_0_10_s=1.85,
            time_0_30_s=65.0,
        )

    assert "menor o igual a 60" in str(exc_info.value)
