"""Tests adicionales para StatisticDAO."""

from unittest.mock import MagicMock

import pytest

from app.dao.statistic_dao import StatisticDAO
from app.models.statistic import Statistic


class TestStatisticDAOInit:
    """Tests para inicialización de StatisticDAO."""

    def test_init(self):
        """Verifica inicialización."""
        dao = StatisticDAO()
        assert dao.model == Statistic


class TestGetClubOverview:
    """Tests para get_club_overview."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return StatisticDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_get_club_overview_basic(self, dao, mock_db):
        """Obtiene métricas básicas del club."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.get_club_overview(mock_db)

        assert isinstance(result, dict)

    def test_get_club_overview_with_type_filter(self, dao, mock_db):
        """Filtra por tipo de atleta."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.get_club_overview(mock_db, type_athlete="UNL")

        assert isinstance(result, dict)

    def test_get_club_overview_with_sex_filter(self, dao, mock_db):
        """Filtra por sexo."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.get_club_overview(mock_db, sex="MALE")

        assert isinstance(result, dict)


class TestGetEvaluationStatistics:
    """Tests para get_evaluation_statistics (si existe)."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return StatisticDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_dao_has_evaluation_methods(self, dao):
        """Verifica que el DAO tenga métodos de estadísticas."""
        # Verificar que existan los métodos esperados
        assert hasattr(dao, "get_club_overview")
        assert callable(dao.get_club_overview)


class TestStatisticDAOInheritance:
    """Tests para verificar herencia de BaseDAO."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return StatisticDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_get_by_id(self, dao, mock_db):
        """Puede obtener estadística por ID."""
        mock_stat = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stat

        result = dao.get_by_id(mock_db, 1)

        assert result == mock_stat

    def test_get_all(self, dao, mock_db):
        """Puede obtener todas las estadísticas."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.get_all(mock_db)

        assert isinstance(result, list)
