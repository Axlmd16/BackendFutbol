"""Tests para TestDAO."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.dao.test_dao import TestDAO
from app.models.test import Test
from app.utils.exceptions import DatabaseException


class TestTestDAOInit:
    """Tests para inicialización de TestDAO."""

    def test_init(self):
        """Verifica inicialización."""
        dao = TestDAO()
        assert dao.model == Test

    def test_test_flag_set(self):
        """Verifica que __test__ está definido para evitar pytest."""
        assert TestDAO.__test__ is False


class TestCreateSprintTest:
    """Tests para create_sprint_test."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_create_sprint_test_success(self, dao, mock_db):
        """Crea SprintTest correctamente."""
        with patch.object(dao, "_validate_test_data"):
            dao.create_sprint_test(
                db=mock_db,
                date=datetime.now(),
                athlete_id=1,
                evaluation_id=1,
                distance_meters=30.0,
                time_0_10_s=2.5,
                time_0_30_s=5.5,
                observations="Test sprint",
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_create_sprint_test_validation_error(self, dao, mock_db):
        """Hace rollback en error de validación."""
        with patch.object(
            dao, "_validate_test_data", side_effect=DatabaseException("Error")
        ):
            with pytest.raises(DatabaseException):
                dao.create_sprint_test(
                    db=mock_db,
                    date=datetime.now(),
                    athlete_id=0,  # inválido
                    evaluation_id=1,
                    distance_meters=30.0,
                    time_0_10_s=2.5,
                    time_0_30_s=5.5,
                )

            mock_db.rollback.assert_called_once()

    def test_create_sprint_test_db_error(self, dao, mock_db):
        """Hace rollback en error de BD."""
        mock_db.add.side_effect = Exception("DB Error")

        with patch.object(dao, "_validate_test_data"):
            with pytest.raises(DatabaseException) as exc_info:
                dao.create_sprint_test(
                    db=mock_db,
                    date=datetime.now(),
                    athlete_id=1,
                    evaluation_id=1,
                    distance_meters=30.0,
                    time_0_10_s=2.5,
                    time_0_30_s=5.5,
                )

            assert "Error al crear SprintTest" in str(exc_info.value)
            mock_db.rollback.assert_called_once()


class TestCreateYoyoTest:
    """Tests para create_yoyo_test."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_create_yoyo_test_success(self, dao, mock_db):
        """Crea YoyoTest correctamente."""
        with patch.object(dao, "_validate_test_data"):
            dao.create_yoyo_test(
                db=mock_db,
                date=datetime.now(),
                athlete_id=1,
                evaluation_id=1,
                shuttle_count=50,
                final_level="16.3",
                failures=2,
                observations="Test yoyo",
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_create_yoyo_test_validation_error(self, dao, mock_db):
        """Hace rollback en error de validación."""
        with patch.object(
            dao, "_validate_test_data", side_effect=DatabaseException("Error")
        ):
            with pytest.raises(DatabaseException):
                dao.create_yoyo_test(
                    db=mock_db,
                    date=datetime.now(),
                    athlete_id=1,
                    evaluation_id=0,  # inválido
                    shuttle_count=50,
                    final_level="16.3",
                    failures=2,
                )

            mock_db.rollback.assert_called_once()

    def test_create_yoyo_test_db_error(self, dao, mock_db):
        """Hace rollback en error de BD."""
        mock_db.add.side_effect = Exception("DB Error")

        with patch.object(dao, "_validate_test_data"):
            with pytest.raises(DatabaseException) as exc_info:
                dao.create_yoyo_test(
                    db=mock_db,
                    date=datetime.now(),
                    athlete_id=1,
                    evaluation_id=1,
                    shuttle_count=50,
                    final_level="16.3",
                    failures=2,
                )

            assert "Error al crear YoyoTest" in str(exc_info.value)
            mock_db.rollback.assert_called_once()


class TestCreateEnduranceTest:
    """Tests para create_endurance_test."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_create_endurance_test_success(self, dao, mock_db):
        """Crea EnduranceTest correctamente."""
        with patch.object(dao, "_validate_test_data"):
            dao.create_endurance_test(
                db=mock_db,
                date=datetime.now(),
                athlete_id=1,
                evaluation_id=1,
                min_duration=12,
                total_distance_m=2400.0,
                observations="Test resistencia",
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_create_endurance_test_db_error(self, dao, mock_db):
        """Hace rollback en error de BD."""
        mock_db.add.side_effect = Exception("DB Error")

        with patch.object(dao, "_validate_test_data"):
            with pytest.raises(DatabaseException) as exc_info:
                dao.create_endurance_test(
                    db=mock_db,
                    date=datetime.now(),
                    athlete_id=1,
                    evaluation_id=1,
                    min_duration=12,
                    total_distance_m=2400.0,
                )

            assert "Error al crear EnduranceTest" in str(exc_info.value)
            mock_db.rollback.assert_called_once()


class TestCreateTechnicalAssessment:
    """Tests para create_technical_assessment."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_create_technical_assessment_success(self, dao, mock_db):
        """Crea TechnicalAssessment correctamente."""
        with patch.object(dao, "_validate_test_data"):
            dao.create_technical_assessment(
                db=mock_db,
                date=datetime.now(),
                athlete_id=1,
                evaluation_id=1,
                ball_control="BUENO",
                short_pass="EXCELENTE",
                long_pass="REGULAR",
                shooting="BUENO",
                dribbling="EXCELENTE",
                observations="Test técnico",
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_create_technical_assessment_db_error(self, dao, mock_db):
        """Hace rollback en error de BD."""
        mock_db.add.side_effect = Exception("DB Error")

        with patch.object(dao, "_validate_test_data"):
            with pytest.raises(DatabaseException) as exc_info:
                dao.create_technical_assessment(
                    db=mock_db, date=datetime.now(), athlete_id=1, evaluation_id=1
                )

            assert "Error al crear TechnicalAssessment" in str(exc_info.value)
            mock_db.rollback.assert_called_once()


class TestTestDAOGetById:
    """Tests para get_by_id."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_get_by_id_found(self, dao, mock_db):
        """Retorna test encontrado."""
        mock_test = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_test

        result = dao.get_by_id(mock_db, 1)

        assert result == mock_test

    def test_get_by_id_not_found(self, dao, mock_db):
        """Retorna None si no existe."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = dao.get_by_id(mock_db, 999)

        assert result is None

    def test_get_by_id_include_inactive(self, dao, mock_db):
        """Incluye inactivos si only_active=False."""
        mock_test = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_test

        result = dao.get_by_id(mock_db, 1, only_active=False)

        assert result == mock_test

    def test_get_by_id_db_error(self, dao, mock_db):
        """Lanza DatabaseException en error."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException) as exc_info:
            dao.get_by_id(mock_db, 1)

        assert "Error al obtener test" in str(exc_info.value)


class TestListByEvaluation:
    """Tests para list_by_evaluation."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_list_by_evaluation_success(self, dao, mock_db):
        """Lista tests de una evaluación."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.list_by_evaluation(mock_db, evaluation_id=1)

        assert isinstance(result, list)

    def test_list_by_evaluation_db_error(self, dao, mock_db):
        """Lanza DatabaseException en error."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException) as exc_info:
            dao.list_by_evaluation(mock_db, evaluation_id=1)

        assert "Error al listar tests de evaluación" in str(exc_info.value)


class TestListByAthlete:
    """Tests para list_by_athlete."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_list_by_athlete_success(self, dao, mock_db):
        """Lista tests de un atleta."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.list_by_athlete(mock_db, athlete_id=1)

        assert isinstance(result, list)

    def test_list_by_athlete_db_error(self, dao, mock_db):
        """Lanza DatabaseException en error."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException) as exc_info:
            dao.list_by_athlete(mock_db, athlete_id=1)

        assert "Error al listar tests del atleta" in str(exc_info.value)


class TestCountByEvaluation:
    """Tests para count_by_evaluation."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_count_by_evaluation_success(self, dao, mock_db):
        """Cuenta tests de una evaluación."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5

        result = dao.count_by_evaluation(mock_db, evaluation_id=1)

        assert result == 5

    def test_count_by_evaluation_db_error(self, dao, mock_db):
        """Lanza DatabaseException en error."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException) as exc_info:
            dao.count_by_evaluation(mock_db, evaluation_id=1)

        assert "Error al contar tests de evaluación" in str(exc_info.value)


class TestTestDAODelete:
    """Tests para delete."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return TestDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_delete_success(self, dao, mock_db):
        """Elimina (soft delete) correctamente."""
        mock_test = MagicMock()

        with patch.object(dao, "get_by_id", return_value=mock_test):
            result = dao.delete(mock_db, test_id=1)

            assert result is True
            assert mock_test.is_active is False
            mock_db.commit.assert_called_once()

    def test_delete_not_found(self, dao, mock_db):
        """Retorna False si no existe."""
        with patch.object(dao, "get_by_id", return_value=None):
            result = dao.delete(mock_db, test_id=999)

            assert result is False

    def test_delete_db_error(self, dao, mock_db):
        """Hace rollback en error."""
        mock_test = MagicMock()

        with patch.object(dao, "get_by_id", return_value=mock_test):
            mock_db.commit.side_effect = Exception("DB Error")

            with pytest.raises(DatabaseException) as exc_info:
                dao.delete(mock_db, test_id=1)

            assert "Error al eliminar test" in str(exc_info.value)
            mock_db.rollback.assert_called_once()


class TestValidateTestData:
    """Tests para _validate_test_data."""

    def test_validate_valid_data(self):
        """Acepta datos válidos."""
        # No debe lanzar excepción
        TestDAO._validate_test_data(athlete_id=1, evaluation_id=1, date=datetime.now())

    def test_validate_invalid_athlete_id_zero(self):
        """Rechaza athlete_id = 0."""
        with pytest.raises(DatabaseException) as exc_info:
            TestDAO._validate_test_data(
                athlete_id=0, evaluation_id=1, date=datetime.now()
            )

        assert "athlete_id inválido" in str(exc_info.value)

    def test_validate_invalid_athlete_id_negative(self):
        """Rechaza athlete_id negativo."""
        with pytest.raises(DatabaseException) as exc_info:
            TestDAO._validate_test_data(
                athlete_id=-1, evaluation_id=1, date=datetime.now()
            )

        assert "athlete_id inválido" in str(exc_info.value)

    def test_validate_invalid_evaluation_id_zero(self):
        """Rechaza evaluation_id = 0."""
        with pytest.raises(DatabaseException) as exc_info:
            TestDAO._validate_test_data(
                athlete_id=1, evaluation_id=0, date=datetime.now()
            )

        assert "evaluation_id inválido" in str(exc_info.value)

    def test_validate_invalid_evaluation_id_negative(self):
        """Rechaza evaluation_id negativo."""
        with pytest.raises(DatabaseException) as exc_info:
            TestDAO._validate_test_data(
                athlete_id=1, evaluation_id=-1, date=datetime.now()
            )

        assert "evaluation_id inválido" in str(exc_info.value)

    def test_validate_missing_date(self):
        """Rechaza fecha None."""
        with pytest.raises(DatabaseException) as exc_info:
            TestDAO._validate_test_data(athlete_id=1, evaluation_id=1, date=None)

        assert "fecha del test es requerida" in str(exc_info.value)
