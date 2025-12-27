from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.schemas.athlete_schema import AthleteInscriptionDTO
from app.utils.exceptions import AlreadyExistsException, ValidationException


@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)


@pytest.fixture
def controller():
    c = AthleteController()
    # Mocks de DAOs
    c.athlete_dao.exists = MagicMock()
    c.athlete_dao.create = MagicMock()
    c.statistic_dao.create = MagicMock()
    return c


@pytest.fixture
def valid_data():
    return AthleteInscriptionDTO(
        first_name="Juan",
        last_name="Pérez",
        dni="1710034065",
        phone="3424123456",
        birth_date="1998-05-15",
        institutional_email="juan.perez@unl.edu.ar",
        university_role="student",
        weight="75.5",
        height="180",
    )


def test_register_athlete_unl_success(controller, mock_db_session, valid_data):
    controller.athlete_dao.exists.side_effect = [False, False]
    controller.athlete_dao.create.return_value = MagicMock(
        id=1,
        first_name="Juan",
        last_name="Pérez",
        institutional_email="juan.perez@unl.edu.ar",
    )
    controller.statistic_dao.create.return_value = MagicMock(id=10)

    result = controller.register_athlete_unl(mock_db_session, valid_data)

    assert result.athlete_id == 1
    assert result.statistic_id == 10
    assert result.first_name == "Juan"
    assert result.last_name == "Pérez"
    assert result.institutional_email == "juan.perez@unl.edu.ar"

    controller.athlete_dao.exists.assert_any_call(mock_db_session, "dni", "1710034065")
    controller.athlete_dao.exists.assert_any_call(
        mock_db_session,
        "institutional_email",
        "juan.perez@unl.edu.ar",
    )
    controller.athlete_dao.create.assert_called_once()
    controller.statistic_dao.create.assert_called_once()


def test_register_athlete_unl_invalid_role(controller, mock_db_session, valid_data):
    valid_data.university_role = "deportista"

    with pytest.raises(ValidationException) as exc:
        controller.register_athlete_unl(mock_db_session, valid_data)

    assert "Rol inválido" in str(exc.value)


def test_register_athlete_unl_duplicate_dni(controller, mock_db_session, valid_data):
    controller.athlete_dao.exists.side_effect = [True, False]

    with pytest.raises(AlreadyExistsException) as exc:
        controller.register_athlete_unl(mock_db_session, valid_data)

    assert "DNI" in str(exc.value)
    controller.athlete_dao.create.assert_not_called()
    controller.statistic_dao.create.assert_not_called()


def test_register_athlete_unl_duplicate_email(controller, mock_db_session, valid_data):
    controller.athlete_dao.exists.side_effect = [False, True]

    with pytest.raises(AlreadyExistsException) as exc:
        controller.register_athlete_unl(mock_db_session, valid_data)

    assert "email" in str(exc.value).lower()
    controller.athlete_dao.create.assert_not_called()
    controller.statistic_dao.create.assert_not_called()


def test_register_athlete_unl_uppercase_role(controller, mock_db_session, valid_data):
    valid_data.university_role = "teacher"  # minúsculas en input
    controller.athlete_dao.exists.side_effect = [False, False]

    # Capturar el payload pasado al DAO
    def _create(_, payload):
        # Assert temprano sobre el rol en mayúsculas
        assert payload["university_role"] == "TEACHER"
        m = MagicMock()
        m.id = 3
        m.first_name = valid_data.first_name
        m.last_name = valid_data.last_name
        m.institutional_email = valid_data.institutional_email
        return m

    controller.athlete_dao.create.side_effect = _create
    controller.statistic_dao.create.return_value = MagicMock(id=30)

    result = controller.register_athlete_unl(mock_db_session, valid_data)
    assert result.athlete_id == 3
