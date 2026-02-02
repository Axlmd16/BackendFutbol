"""Tests unitarios para `YoyoTestController`."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

import pytest
from pydantic import ValidationError

from app.controllers.yoyo_test_controller import YoyoTestController
from app.models.evaluation import Evaluation
from app.models.yoyo_test import YoyoTest
from app.schemas.yoyo_test_schema import CreateYoyoTestSchema, UpdateYoyoTestSchema

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def yoyo_test_controller():
    """Fixture para YoyoTestController con DAOs mockeados."""
    controller = YoyoTestController()
    controller.yoyo_test_dao = MagicMock()
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
def mock_yoyo_test():
    """Fixture de un Yoyo Test mock."""
    test = Mock(spec=YoyoTest)
    test.id = 2
    test.type = "yoyo_test"
    test.date = datetime.now()
    test.athlete_id = 5
    test.evaluation_id = 1
    test.shuttle_count = 47
    test.final_level = "18.2"
    test.failures = 2
    test.observations = "Excellent aerobic capacity"
    test.is_active = True
    return test


# ==============================================
# TESTS: ADD YOYO TEST
# ==============================================


def test_add_yoyo_test_success(
    yoyo_test_controller, mock_db, mock_evaluation, mock_athlete, mock_yoyo_test
):
    """Agregar Yoyo Test exitosamente."""
    yoyo_test_controller.evaluation_dao.get_by_id.return_value = mock_evaluation
    yoyo_test_controller.athlete_dao.get_by_id.return_value = mock_athlete
    yoyo_test_controller.test_dao.create_yoyo_test.return_value = mock_yoyo_test

    payload = CreateYoyoTestSchema(
        evaluation_id=1,
        athlete_id=5,
        date=mock_yoyo_test.date,
        shuttle_count=47,
        final_level="18.2",
        failures=2,
        observations="Excellent aerobic capacity",
    )

    result = yoyo_test_controller.add_test(
        db=mock_db,
        payload=payload,
    )

    assert result.id == 2
    assert result.type == "yoyo_test"
    assert result.shuttle_count == 47
    yoyo_test_controller.test_dao.create_yoyo_test.assert_called_once()


# ==============================================
# TESTS: UPDATE YOYO TEST
# ==============================================


def test_update_yoyo_test_success(yoyo_test_controller, mock_db, mock_yoyo_test):
    """Actualizar campos de un Yoyo Test existente."""
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = mock_yoyo_test
    updated = Mock()
    updated.id = mock_yoyo_test.id
    updated.shuttle_count = 55
    yoyo_test_controller.yoyo_test_dao.update.return_value = updated

    payload = UpdateYoyoTestSchema(
        shuttle_count=55,
        observations="Mejoró",
    )

    result = yoyo_test_controller.update_test(
        db=mock_db,
        test_id=2,
        payload=payload,
    )

    assert result.shuttle_count == 55
    yoyo_test_controller.yoyo_test_dao.update.assert_called_once_with(
        mock_db, 2, {"shuttle_count": 55, "observations": "Mejoró"}
    )


def test_update_yoyo_test_no_fields_returns_existing(
    yoyo_test_controller, mock_db, mock_yoyo_test
):
    """Si no se envían campos, devuelve la instancia actual."""
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = mock_yoyo_test

    payload = UpdateYoyoTestSchema()

    result = yoyo_test_controller.update_test(
        db=mock_db,
        test_id=2,
        payload=payload,
    )

    assert result is mock_yoyo_test
    yoyo_test_controller.yoyo_test_dao.update.assert_not_called()


# ==============================================
# TESTS: DELETE YOYO TEST
# ==============================================


def test_delete_yoyo_test_success(
    monkeypatch, yoyo_test_controller, mock_db, mock_yoyo_test
):
    """Elimina y actualiza estadísticas cuando existe."""
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = mock_yoyo_test
    yoyo_test_controller.yoyo_test_dao.delete.return_value = None

    called = {"stats": False}

    def _update_stats(db, athlete_id):
        called["stats"] = True
        assert athlete_id == mock_yoyo_test.athlete_id

    monkeypatch.setattr(
        "app.controllers.yoyo_test_controller.statistic_controller.update_athlete_stats",
        _update_stats,
    )

    result = yoyo_test_controller.delete_test(mock_db, test_id=2)

    assert result is True
    yoyo_test_controller.yoyo_test_dao.delete.assert_called_once_with(mock_db, 2)
    assert called["stats"] is True


def test_delete_yoyo_test_not_found(yoyo_test_controller, mock_db):
    """Si no existe retorna False y no borra."""
    yoyo_test_controller.yoyo_test_dao.get_by_id.return_value = None

    result = yoyo_test_controller.delete_test(mock_db, test_id=999)

    assert result is False
    yoyo_test_controller.yoyo_test_dao.delete.assert_not_called()


# ==============================================
# TESTS: LIST YOYO TESTS
# ==============================================


def test_list_tests_success(yoyo_test_controller, mock_db, mock_yoyo_test):
    """Lista yoyo tests con paginación y filtros."""
    from app.schemas.yoyo_test_schema import YoyoTestFilter

    # Mock query chain
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_with_entities = MagicMock()
    mock_order = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.with_entities.return_value = mock_with_entities
    mock_with_entities.scalar.return_value = 5
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = [mock_yoyo_test]

    filters = YoyoTestFilter(page=1, limit=10)
    items, total = yoyo_test_controller.list_tests(mock_db, filters)

    assert len(items) == 1
    assert total == 5
    assert items[0] is mock_yoyo_test


def test_list_tests_with_filters(yoyo_test_controller, mock_db):
    """Lista yoyo tests filtrando por evaluation_id y athlete_id."""
    from app.schemas.yoyo_test_schema import YoyoTestFilter

    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_with_entities = MagicMock()
    mock_order = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter  # Para encadenar filters
    mock_filter.with_entities.return_value = mock_with_entities
    mock_with_entities.scalar.return_value = 2
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = []

    filters = YoyoTestFilter(page=1, limit=10, evaluation_id=1, athlete_id=5)
    items, total = yoyo_test_controller.list_tests(mock_db, filters)

    assert items == []
    assert total == 2


def test_list_tests_with_search(yoyo_test_controller, mock_db, mock_yoyo_test):
    """Lista yoyo tests filtrando por nombre de atleta (search)."""
    from app.schemas.yoyo_test_schema import YoyoTestFilter

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
    mock_limit.all.return_value = [mock_yoyo_test]

    filters = YoyoTestFilter(page=1, limit=10, search="Juan")
    items, total = yoyo_test_controller.list_tests(mock_db, filters)

    assert len(items) == 1
    assert total == 1


def test_list_tests_with_empty_search(yoyo_test_controller, mock_db):
    """Lista yoyo tests con search vacío trae todos los registros."""
    from app.schemas.yoyo_test_schema import YoyoTestFilter

    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_with_entities = MagicMock()
    mock_order = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.with_entities.return_value = mock_with_entities
    mock_with_entities.scalar.return_value = 5
    mock_filter.order_by.return_value = mock_order
    mock_order.offset.return_value = mock_offset
    mock_offset.limit.return_value = mock_limit
    mock_limit.all.return_value = []

    filters = YoyoTestFilter(page=1, limit=10, search="")
    items, total = yoyo_test_controller.list_tests(mock_db, filters)

    assert items == []
    assert total == 5


def test_list_tests_with_search_no_match(yoyo_test_controller, mock_db):
    """Lista yoyo tests con search que no coincide devuelve lista vacía."""
    from app.schemas.yoyo_test_schema import YoyoTestFilter

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

    filters = YoyoTestFilter(page=1, limit=10, search="NoExiste")
    items, total = yoyo_test_controller.list_tests(mock_db, filters)

    assert items == []


# ==============================================
# TESTS: VALIDACIONES
# ==============================================


def test_yoyo_test_future_date_rejected():
    """Validación: La fecha del test no puede ser futura."""
    future_date = datetime.now() + timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        CreateYoyoTestSchema(
            date=future_date,
            athlete_id=1,
            evaluation_id=1,
            shuttle_count=47,
            final_level="18.2",
            failures=2,
        )

    assert "La fecha del test no puede ser futura" in str(exc_info.value)


def test_yoyo_test_valid_format_xx_y():
    """Validación: Formato válido XX.Y."""
    schema = CreateYoyoTestSchema(
        date=datetime.now(),
        athlete_id=1,
        evaluation_id=1,
        shuttle_count=47,
        final_level="18.2",
        failures=2,
    )

    assert schema.final_level == "18.2"


def test_yoyo_test_valid_format_x_y():
    """Validación: Formato válido X.Y."""
    schema = CreateYoyoTestSchema(
        date=datetime.now(),
        athlete_id=1,
        evaluation_id=1,
        shuttle_count=47,
        final_level="9.5",
        failures=2,
    )

    assert schema.final_level == "9.5"


def test_yoyo_test_invalid_format_no_decimal():
    """Validación: Rechaza formato sin decimal."""
    with pytest.raises(ValidationError) as exc_info:
        CreateYoyoTestSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            shuttle_count=47,
            final_level="18",
            failures=2,
        )

    assert "debe tener el formato XX.Y" in str(exc_info.value)


def test_yoyo_test_invalid_format_two_decimals():
    """Validación: Rechaza formato con dos decimales."""
    with pytest.raises(ValidationError) as exc_info:
        CreateYoyoTestSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            shuttle_count=47,
            final_level="18.25",
            failures=2,
        )

    assert "debe tener el formato XX.Y" in str(exc_info.value)


def test_yoyo_test_invalid_format_text():
    """Validación: Rechaza texto inválido."""
    with pytest.raises(ValidationError) as exc_info:
        CreateYoyoTestSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            shuttle_count=47,
            final_level="nivel18",
            failures=2,
        )

    assert "debe tener el formato XX.Y" in str(exc_info.value)


def test_yoyo_test_shuttle_count_limit():
    """Validación: Máximo 1000 shuttles."""
    with pytest.raises(ValidationError) as exc_info:
        CreateYoyoTestSchema(
            date=datetime.now(),
            athlete_id=1,
            evaluation_id=1,
            shuttle_count=1500,
            final_level="18.2",
            failures=2,
        )

    assert "menor o igual a 1000" in str(exc_info.value)


def test_yoyo_test_valid_edge_cases():
    """Validación: Casos válidos en límites."""
    schema = CreateYoyoTestSchema(
        date=datetime.now(),
        athlete_id=1,
        evaluation_id=1,
        shuttle_count=1000,
        final_level="99.9",
        failures=0,
    )

    assert schema.shuttle_count == 1000
    assert schema.final_level == "99.9"
