"""Tests para BaseDAO."""

from unittest.mock import MagicMock

import pytest

from app.dao.base import BaseDAO
from app.utils.exceptions import DatabaseException


class MockModel:
    """Modelo mock para tests."""

    __name__ = "MockModel"
    id = None
    is_active = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestBaseDAOInit:
    """Tests para inicialización de BaseDAO."""

    def test_init_with_model(self):
        """Verifica inicialización con modelo."""
        dao = BaseDAO(MockModel)
        assert dao.model == MockModel


class TestBaseDAOGetAll:
    """Tests para get_all."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        db = MagicMock()
        return db

    def test_get_all_success(self, dao, mock_db):
        """Obtiene todos los registros exitosamente."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [MockModel(id=1), MockModel(id=2)]

        result = dao.get_all(mock_db)

        assert len(result) == 2

    def test_get_all_with_pagination(self, dao, mock_db):
        """Obtiene registros con paginación."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        dao.get_all(mock_db, skip=10, limit=5)

        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(5)

    def test_get_all_only_active_false(self, dao, mock_db):
        """Obtiene todos incluyendo inactivos."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        dao.get_all(mock_db, only_active=False)

        # No debería filtrar por is_active
        mock_query.filter.assert_not_called()

    def test_get_all_database_error(self, dao, mock_db):
        """Maneja error de base de datos."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException):
            dao.get_all(mock_db)


class TestBaseDAOGetById:
    """Tests para get_by_id."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_get_by_id_found(self, dao, mock_db):
        """Encuentra registro por ID."""
        mock_obj = MockModel(id=1)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_obj

        result = dao.get_by_id(mock_db, 1)

        assert result.id == 1

    def test_get_by_id_not_found(self, dao, mock_db):
        """Retorna None si no encuentra."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = dao.get_by_id(mock_db, 999)

        assert result is None

    def test_get_by_id_database_error(self, dao, mock_db):
        """Maneja error de base de datos."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException):
            dao.get_by_id(mock_db, 1)


class TestBaseDAOCreate:
    """Tests para create."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_create_success(self, dao, mock_db):
        """Crea registro exitosamente."""
        data = {"name": "Test"}

        dao.create(mock_db, data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_database_error(self, dao, mock_db):
        """Maneja error de base de datos al crear."""
        mock_db.add.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException):
            dao.create(mock_db, {"name": "Test"})

        mock_db.rollback.assert_called_once()


class TestBaseDAOUpdate:
    """Tests para update."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_update_success(self, dao, mock_db):
        """Actualiza registro exitosamente."""
        mock_obj = MockModel(id=1, name="Old")
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_obj

        dao.update(mock_db, 1, {"name": "New"})

        mock_db.commit.assert_called_once()

    def test_update_not_found(self, dao, mock_db):
        """Retorna None si no encuentra."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = dao.update(mock_db, 999, {"name": "New"})

        assert result is None

    def test_update_exclude_none(self, dao, mock_db):
        """Excluye valores None por defecto."""
        mock_obj = MockModel(id=1, name="Old", desc="Desc")
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_obj

        dao.update(mock_db, 1, {"name": "New", "desc": None})

        # desc no debería haber cambiado
        assert mock_obj.desc == "Desc"

    def test_update_database_error(self, dao, mock_db):
        """Maneja error de base de datos al actualizar."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MockModel(id=1)
        mock_db.commit.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException):
            dao.update(mock_db, 1, {"name": "New"})


class TestBaseDAODelete:
    """Tests para delete."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_soft_delete_success(self, dao, mock_db):
        """Soft delete exitoso."""
        mock_obj = MockModel(id=1, is_active=True)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_obj

        result = dao.delete(mock_db, 1, soft_delete=True)

        assert result is True
        assert mock_obj.is_active is False

    def test_hard_delete_success(self, dao, mock_db):
        """Hard delete exitoso."""
        mock_obj = MockModel(id=1)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_obj

        result = dao.delete(mock_db, 1, soft_delete=False)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_obj)

    def test_delete_not_found(self, dao, mock_db):
        """Retorna False si no encuentra."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = dao.delete(mock_db, 999)

        assert result is False

    def test_delete_database_error(self, dao, mock_db):
        """Maneja error de base de datos al eliminar."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MockModel(id=1)
        mock_db.commit.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException):
            dao.delete(mock_db, 1)


class TestBaseDAOGetByField:
    """Tests para get_by_field."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_get_by_field_success(self, dao, mock_db):
        """Obtiene por campo exitosamente."""
        mock_obj = MockModel(id=1)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_obj

        # Agregar el campo al modelo
        MockModel.email = "test@test.com"
        result = dao.get_by_field(mock_db, "email", "test@test.com")

        assert result is not None

    def test_get_by_field_invalid_field(self, dao, mock_db):
        """Error si el campo no existe."""
        with pytest.raises(DatabaseException):
            dao.get_by_field(mock_db, "nonexistent_field", "value")


class TestBaseDAOExists:
    """Tests para exists."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_exists_true(self, dao, mock_db):
        """Retorna True si existe."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MockModel(id=1)

        MockModel.email = "test@test.com"
        result = dao.exists(mock_db, "email", "test@test.com")

        assert result is True

    def test_exists_false(self, dao, mock_db):
        """Retorna False si no existe."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        MockModel.email = None
        result = dao.exists(mock_db, "email", "nonexistent@test.com")

        assert result is False

    def test_exists_invalid_field(self, dao, mock_db):
        """Retorna False si el campo no existe."""
        result = dao.exists(mock_db, "nonexistent_field", "value")
        assert result is False


class TestBaseDAOCount:
    """Tests para count."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_count_success(self, dao, mock_db):
        """Cuenta registros exitosamente."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5

        result = dao.count(mock_db)

        assert result == 5

    def test_count_error_returns_zero(self, dao, mock_db):
        """Retorna 0 en caso de error."""
        mock_db.query.side_effect = Exception("DB Error")

        result = dao.count(mock_db)

        assert result == 0


class TestBaseDAOSearch:
    """Tests para search."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_search_with_filters(self, dao, mock_db):
        """Busca con filtros."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        MockModel.status = "active"
        result = dao.search(mock_db, filters={"status": "active"})

        assert result == []

    def test_search_with_ordering(self, dao, mock_db):
        """Busca con ordenamiento."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.search(mock_db, order_by="id", order_dir="desc")

        assert result == []


class TestBaseDAOBulkCreate:
    """Tests para bulk_create."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        return BaseDAO(MockModel)

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_bulk_create_success(self, dao, mock_db):
        """Crea múltiples registros exitosamente."""
        data = [{"name": "Test1"}, {"name": "Test2"}]

        dao.bulk_create(mock_db, data)

        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_bulk_create_error(self, dao, mock_db):
        """Maneja error en bulk create."""
        mock_db.add_all.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException):
            dao.bulk_create(mock_db, [{"name": "Test"}])

        mock_db.rollback.assert_called_once()


class TestBaseDAOBulkUpdate:
    """Tests para bulk_update."""

    @pytest.fixture
    def dao(self):
        """DAO con modelo mock."""
        dao = BaseDAO(MockModel)
        return dao

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_bulk_update_success(self, dao, mock_db):
        """Actualiza múltiples registros exitosamente."""
        mock_obj = MockModel(id=1, name="Old")
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_obj

        updates = [{"id": 1, "name": "New1"}, {"id": 2, "name": "New2"}]

        result = dao.bulk_update(mock_db, updates)

        assert result is True

    def test_bulk_update_skips_without_id(self, dao, mock_db):
        """Ignora actualizaciones sin ID."""
        updates = [{"name": "No ID"}]

        result = dao.bulk_update(mock_db, updates)

        assert result is True
