"""Tests para UserDAO."""

from unittest.mock import MagicMock

import pytest

from app.dao.user_dao import UserDAO
from app.models.enums.rol import Role
from app.models.user import User


class TestUserDAOInit:
    """Tests para inicialización de UserDAO."""

    def test_init(self):
        """Verifica inicialización."""
        dao = UserDAO()
        assert dao.model == User


class TestResolveRole:
    """Tests para _resolve_role."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return UserDAO()

    def test_resolve_role_empty_string(self, dao):
        """Retorna None para string vacío."""
        result = dao._resolve_role("")
        assert result is None

    def test_resolve_role_none(self, dao):
        """Retorna None para None."""
        result = dao._resolve_role(None)
        assert result is None

    def test_resolve_role_alias_admin(self, dao):
        """Resuelve alias 'admin'."""
        result = dao._resolve_role("admin")
        assert result == Role.ADMINISTRATOR

    def test_resolve_role_alias_administrator(self, dao):
        """Resuelve alias 'administrator'."""
        result = dao._resolve_role("administrator")
        assert result == Role.ADMINISTRATOR

    def test_resolve_role_alias_entrenador(self, dao):
        """Resuelve alias 'entrenador'."""
        result = dao._resolve_role("entrenador")
        assert result == Role.COACH

    def test_resolve_role_alias_coach(self, dao):
        """Resuelve alias 'coach'."""
        result = dao._resolve_role("coach")
        assert result == Role.COACH

    def test_resolve_role_alias_pasante(self, dao):
        """Resuelve alias 'pasante'."""
        result = dao._resolve_role("pasante")
        assert result == Role.INTERN

    def test_resolve_role_alias_intern(self, dao):
        """Resuelve alias 'intern'."""
        result = dao._resolve_role("intern")
        assert result == Role.INTERN

    def test_resolve_role_case_insensitive(self, dao):
        """Resuelve alias ignorando mayúsculas/minúsculas."""
        result = dao._resolve_role("ADMIN")
        assert result == Role.ADMINISTRATOR

        result = dao._resolve_role("Coach")
        assert result == Role.COACH

    def test_resolve_role_with_spaces(self, dao):
        """Resuelve alias con espacios."""
        result = dao._resolve_role("  admin  ")
        assert result == Role.ADMINISTRATOR

    def test_resolve_role_direct_enum_value(self, dao):
        """Resuelve valor directo del enum."""
        result = dao._resolve_role("Administrator")
        assert result == Role.ADMINISTRATOR

    def test_resolve_role_enum_name(self, dao):
        """Resuelve por nombre del enum."""
        result = dao._resolve_role("ADMINISTRATOR")
        assert result == Role.ADMINISTRATOR

    def test_resolve_role_invalid(self, dao):
        """Retorna None para rol inválido."""
        result = dao._resolve_role("invalid_role")
        assert result is None


class TestGetAllWithFilters:
    """Tests para get_all_with_filters."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return UserDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    @pytest.fixture
    def mock_filters(self):
        """Filtros mock."""
        filters = MagicMock()
        filters.is_active = None
        filters.role = None
        filters.search = None
        filters.skip = 0
        filters.limit = 10
        return filters

    def test_get_all_with_filters_no_filters(self, dao, mock_db, mock_filters):
        """Obtiene todos sin filtros."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 2

    def test_get_all_with_filters_is_active(self, dao, mock_db, mock_filters):
        """Filtra por is_active."""
        mock_filters.is_active = True
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 1

    def test_get_all_with_filters_role(self, dao, mock_db, mock_filters):
        """Filtra por rol."""
        mock_filters.role = "admin"
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 1

    def test_get_all_with_filters_search(self, dao, mock_db, mock_filters):
        """Filtra por búsqueda."""
        mock_filters.search = "Juan"
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 1


class TestGetInternsWithFilters:
    """Tests para get_interns_with_filters."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return UserDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    @pytest.fixture
    def mock_filters(self):
        """Filtros mock."""
        filters = MagicMock()
        filters.search = None
        filters.skip = 0
        filters.limit = 10
        return filters

    def test_get_interns_with_filters_no_search(self, dao, mock_db, mock_filters):
        """Obtiene pasantes sin búsqueda."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_interns_with_filters(mock_db, mock_filters)

        assert total == 3

    def test_get_interns_with_filters_with_search(self, dao, mock_db, mock_filters):
        """Obtiene pasantes con búsqueda."""
        mock_filters.search = "Pedro"
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_interns_with_filters(mock_db, mock_filters)

        assert total == 1
