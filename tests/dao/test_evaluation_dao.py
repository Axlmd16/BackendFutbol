"""Tests para EvaluationDAO."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.dao.evaluation_dao import EvaluationDAO
from app.models.evaluation import Evaluation
from app.utils.exceptions import DatabaseException


class TestEvaluationDAOInit:
    """Tests para inicialización de EvaluationDAO."""

    def test_init(self):
        """Verifica inicialización."""
        dao = EvaluationDAO()
        assert dao.model == Evaluation


class TestEvaluationDAOCreate:
    """Tests para método create."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return EvaluationDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    @pytest.fixture
    def valid_date(self):
        """Fecha válida (futura)."""
        return datetime.now() + timedelta(days=1)

    def test_create_success(self, dao, mock_db, valid_date):
        """Crea evaluación correctamente."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(dao, "_validate_date"):
            with patch.object(dao, "_validate_duplicate_evaluation"):
                dao.create(
                    db=mock_db,
                    name="Evaluación 1",
                    date=valid_date,
                    time="10:00",
                    user_id=1,
                    location="Campo 1",
                    observations="Test",
                )

                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()

    def test_create_validation_error_rollback(self, dao, mock_db, valid_date):
        """Hace rollback en error de validación."""
        with patch.object(
            dao, "_validate_date", side_effect=DatabaseException("Fecha inválida")
        ):
            with pytest.raises(DatabaseException):
                dao.create(
                    db=mock_db,
                    name="Evaluación 1",
                    date=valid_date,
                    time="10:00",
                    user_id=1,
                )

            mock_db.rollback.assert_called_once()

    def test_create_generic_error_rollback(self, dao, mock_db, valid_date):
        """Hace rollback en error genérico."""
        mock_db.add.side_effect = Exception("DB Error")

        with patch.object(dao, "_validate_date"):
            with patch.object(dao, "_validate_duplicate_evaluation"):
                with pytest.raises(DatabaseException) as exc_info:
                    dao.create(
                        db=mock_db,
                        name="Evaluación 1",
                        date=valid_date,
                        time="10:00",
                        user_id=1,
                    )

                assert "Error al crear evaluación" in str(exc_info.value)
                mock_db.rollback.assert_called_once()


class TestEvaluationDAOGetById:
    """Tests para método get_by_id."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return EvaluationDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_get_by_id_found_active(self, dao, mock_db):
        """Retorna evaluación activa encontrada."""
        mock_evaluation = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_evaluation

        result = dao.get_by_id(mock_db, 1, only_active=True)

        assert result == mock_evaluation

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
        mock_evaluation = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_evaluation

        result = dao.get_by_id(mock_db, 1, only_active=False)

        assert result == mock_evaluation

    def test_get_by_id_db_error(self, dao, mock_db):
        """Lanza DatabaseException en error."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException) as exc_info:
            dao.get_by_id(mock_db, 1)

        assert "Error al obtener evaluación" in str(exc_info.value)


class TestEvaluationDAOListAll:
    """Tests para método list_all."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return EvaluationDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_list_all_active(self, dao, mock_db):
        """Lista evaluaciones activas."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.list_all(mock_db, only_active=True)

        assert isinstance(result, list)

    def test_list_all_with_pagination(self, dao, mock_db):
        """Aplica paginación."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        dao.list_all(mock_db, skip=10, limit=5)

        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(5)

    def test_list_all_db_error(self, dao, mock_db):
        """Lanza DatabaseException en error."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException) as exc_info:
            dao.list_all(mock_db)

        assert "Error al listar evaluaciones" in str(exc_info.value)


class TestEvaluationDAOListByUser:
    """Tests para método list_by_user."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return EvaluationDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_list_by_user_success(self, dao, mock_db):
        """Lista evaluaciones de un usuario."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = dao.list_by_user(mock_db, user_id=1)

        assert isinstance(result, list)

    def test_list_by_user_db_error(self, dao, mock_db):
        """Lanza DatabaseException en error."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException) as exc_info:
            dao.list_by_user(mock_db, user_id=1)

        assert "Error al listar evaluaciones del usuario" in str(exc_info.value)


class TestEvaluationDAOUpdate:
    """Tests para método update."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return EvaluationDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_update_success(self, dao, mock_db):
        """Actualiza evaluación correctamente."""
        mock_evaluation = MagicMock()

        with patch.object(dao, "get_by_id", return_value=mock_evaluation):
            result = dao.update(db=mock_db, evaluation_id=1, name="Nuevo nombre")

            assert result == mock_evaluation
            assert mock_evaluation.name == "Nuevo nombre"
            mock_db.commit.assert_called_once()

    def test_update_not_found(self, dao, mock_db):
        """Retorna None si no existe."""
        with patch.object(dao, "get_by_id", return_value=None):
            result = dao.update(mock_db, evaluation_id=999)

            assert result is None

    def test_update_with_date_validation(self, dao, mock_db):
        """Valida fecha si se proporciona."""
        mock_evaluation = MagicMock()
        future_date = datetime.now() + timedelta(days=1)

        with patch.object(dao, "get_by_id", return_value=mock_evaluation):
            with patch.object(dao, "_validate_date") as mock_validate:
                dao.update(mock_db, evaluation_id=1, date=future_date)

                mock_validate.assert_called_once_with(future_date)

    def test_update_db_error(self, dao, mock_db):
        """Hace rollback en error."""
        mock_evaluation = MagicMock()

        with patch.object(dao, "get_by_id", return_value=mock_evaluation):
            mock_db.commit.side_effect = Exception("DB Error")

            with pytest.raises(DatabaseException) as exc_info:
                dao.update(mock_db, evaluation_id=1, name="Test")

            assert "Error al actualizar evaluación" in str(exc_info.value)
            mock_db.rollback.assert_called_once()


class TestEvaluationDAODelete:
    """Tests para método delete."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return EvaluationDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_delete_success(self, dao, mock_db):
        """Elimina (soft delete) correctamente."""
        mock_evaluation = MagicMock()

        with patch.object(dao, "get_by_id", return_value=mock_evaluation):
            result = dao.delete(mock_db, evaluation_id=1)

            assert result is True
            assert mock_evaluation.is_active is False
            mock_db.commit.assert_called_once()

    def test_delete_not_found(self, dao, mock_db):
        """Retorna False si no existe."""
        with patch.object(dao, "get_by_id", return_value=None):
            result = dao.delete(mock_db, evaluation_id=999)

            assert result is False

    def test_delete_db_error(self, dao, mock_db):
        """Hace rollback en error."""
        mock_evaluation = MagicMock()

        with patch.object(dao, "get_by_id", return_value=mock_evaluation):
            mock_db.commit.side_effect = Exception("DB Error")

            with pytest.raises(DatabaseException) as exc_info:
                dao.delete(mock_db, evaluation_id=1)

            assert "Error al eliminar evaluación" in str(exc_info.value)
            mock_db.rollback.assert_called_once()


class TestEvaluationDAOCountEvaluations:
    """Tests para método count_evaluations."""

    @pytest.fixture
    def dao(self):
        """DAO para tests."""
        return EvaluationDAO()

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_count_active(self, dao, mock_db):
        """Cuenta evaluaciones activas."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5

        result = dao.count_evaluations(mock_db, only_active=True)

        assert result == 5

    def test_count_all(self, dao, mock_db):
        """Cuenta todas las evaluaciones."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 10

        result = dao.count_evaluations(mock_db, only_active=False)

        assert result == 10

    def test_count_db_error(self, dao, mock_db):
        """Lanza DatabaseException en error."""
        mock_db.query.side_effect = Exception("DB Error")

        with pytest.raises(DatabaseException) as exc_info:
            dao.count_evaluations(mock_db)

        assert "Error al contar evaluaciones" in str(exc_info.value)


class TestEvaluationDAOValidateDate:
    """Tests para _validate_date."""

    def test_validate_date_future(self):
        """Acepta fecha futura."""
        future_date = datetime.now() + timedelta(days=1)
        # No debe lanzar excepción
        EvaluationDAO._validate_date(future_date)

    def test_validate_date_today(self):
        """Acepta fecha de hoy."""
        today = datetime.now()
        # No debe lanzar excepción
        EvaluationDAO._validate_date(today)

    def test_validate_date_past(self):
        """Rechaza fecha pasada."""
        past_date = datetime.now() - timedelta(days=1)

        with pytest.raises(DatabaseException) as exc_info:
            EvaluationDAO._validate_date(past_date)

        assert "no puede ser anterior a hoy" in str(exc_info.value)


class TestEvaluationDAOValidateDuplicateEvaluation:
    """Tests para _validate_duplicate_evaluation."""

    @pytest.fixture
    def mock_db(self):
        """Session mock."""
        return MagicMock()

    def test_validate_no_duplicate(self, mock_db):
        """Acepta si no hay duplicado."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        future_date = datetime.now() + timedelta(days=1)

        # No debe lanzar excepción
        EvaluationDAO._validate_duplicate_evaluation(mock_db, "Test", future_date, 1)

    def test_validate_duplicate_exists(self, mock_db):
        """Rechaza si existe duplicado."""
        mock_existing = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing

        future_date = datetime.now() + timedelta(days=1)

        with pytest.raises(DatabaseException) as exc_info:
            EvaluationDAO._validate_duplicate_evaluation(
                mock_db, "Test", future_date, 1
            )

        assert "Ya existe una evaluación" in str(exc_info.value)
