"""Tests para AthleteDAO."""

from unittest.mock import MagicMock

import pytest

from app.dao.athlete_dao import AthleteDAO
from app.models.athlete import Athlete
from app.models.enums.sex import Sex


class TestAthleteDAOInit:
    """Tests para inicialización de AthleteDAO."""

    def test_init(self):
        """Verifica inicialización."""
        dao = AthleteDAO()
        assert dao.model == Athlete


class TestGetAllWithFilters:
    """Tests para get_all_with_filters."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return AthleteDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    @pytest.fixture
    def mock_filters(self):
        """Filtros mock básicos."""
        filters = MagicMock()
        filters.search = None
        filters.type_athlete = None
        filters.sex = None
        filters.is_active = None
        filters.skip = 0
        filters.limit = 10
        return filters

    def test_get_all_no_filters(self, dao, mock_db, mock_filters):
        """Obtiene todos los atletas sin filtros."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 5
        mock_db.query.assert_called_once_with(Athlete)

    def test_get_all_with_search(self, dao, mock_db, mock_filters):
        """Filtra por búsqueda (nombre o DNI)."""
        mock_filters.search = "Juan"
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 2
        mock_query.filter.assert_called()

    def test_get_all_with_search_whitespace(self, dao, mock_db, mock_filters):
        """Filtra por búsqueda con espacios."""
        mock_filters.search = "  María  "
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

    def test_get_all_with_type_athlete_string(self, dao, mock_db, mock_filters):
        """Filtra por tipo de atleta (string)."""
        mock_filters.type_athlete = "UNL"
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 3

    def test_get_all_with_type_athlete_enum(self, dao, mock_db, mock_filters):
        """Filtra por tipo de atleta (enum con value)."""
        mock_enum = MagicMock()
        mock_enum.value = "MINOR"
        mock_filters.type_athlete = mock_enum
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 4
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 4

    def test_get_all_with_sex_enum(self, dao, mock_db, mock_filters):
        """Filtra por sexo (enum)."""
        mock_filters.sex = Sex.MALE
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 2

    def test_get_all_with_sex_string_male(self, dao, mock_db, mock_filters):
        """Filtra por sexo (string 'MALE')."""
        mock_filters.sex = "MALE"
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 3

    def test_get_all_with_sex_string_female(self, dao, mock_db, mock_filters):
        """Filtra por sexo (string 'FEMALE')."""
        mock_filters.sex = "FEMALE"
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 2

    def test_get_all_with_sex_invalid_string(self, dao, mock_db, mock_filters):
        """Filtra por sexo con string inválido (no aplica filtro)."""
        mock_filters.sex = "INVALID_SEX"
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 5

    def test_get_all_with_is_active_true(self, dao, mock_db, mock_filters):
        """Filtra por is_active=True."""
        mock_filters.is_active = True
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 4
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 4

    def test_get_all_with_is_active_false(self, dao, mock_db, mock_filters):
        """Filtra por is_active=False."""
        mock_filters.is_active = False
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

    def test_get_all_with_multiple_filters(self, dao, mock_db, mock_filters):
        """Filtra con múltiples filtros."""
        mock_filters.search = "Pedro"
        mock_filters.type_athlete = "UNL"
        mock_filters.sex = Sex.MALE
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

    def test_get_all_with_pagination(self, dao, mock_db, mock_filters):
        """Aplica paginación correctamente."""
        mock_filters.skip = 10
        mock_filters.limit = 5
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 20
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert total == 20
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(5)

    def test_get_all_filters_missing_skip_limit(self, dao, mock_db):
        """Usa valores por defecto si skip/limit no existen."""
        # Crear objeto de filtros sin skip/limit
        filters = MagicMock(spec=[])
        filters.search = None
        filters.type_athlete = None
        filters.sex = None
        filters.is_active = None
        # No tiene skip ni limit

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        items, total = dao.get_all_with_filters(mock_db, filters)

        assert total == 3
        # Verifica que usa valores por defecto
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(10)

    def test_get_all_returns_items_list(self, dao, mock_db, mock_filters):
        """Retorna la lista de items."""
        mock_athlete1 = MagicMock()
        mock_athlete2 = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_athlete1, mock_athlete2]

        items, total = dao.get_all_with_filters(mock_db, mock_filters)

        assert len(items) == 2
        assert items[0] == mock_athlete1
        assert items[1] == mock_athlete2
