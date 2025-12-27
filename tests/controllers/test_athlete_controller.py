from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.schemas.athlete_schema import AthleteInscriptionDTO
from app.utils.exceptions import AlreadyExistsException


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
    # Mock de PersonMSService
    c.person_ms_service.create_or_get_person = AsyncMock(
        return_value="12345678-1234-1234-1234-123456789012"
    )
    return c


@pytest.fixture
def valid_data():
    return AthleteInscriptionDTO(
        first_name="Juan",
        last_name="Pérez",
        dni="1710034065",
        phone="3424123456",
        birth_date="1998-05-15",
        weight=75.5,
        height=180.0,
    )


@pytest.mark.asyncio
async def test_register_athlete_unl_success(controller, mock_db_session, valid_data):
    """Test exitoso de registro de atleta."""
    controller.athlete_dao.exists.return_value = False
    controller.athlete_dao.create.return_value = MagicMock(
        id=1,
        full_name="Juan Pérez",
        dni="1710034065",
    )
    controller.statistic_dao.create.return_value = MagicMock(id=10)

    result = await controller.register_athlete_unl(mock_db_session, valid_data)

    assert result.athlete_id == 1
    assert result.statistic_id == 10
    assert result.full_name == "Juan Pérez"
    assert result.dni == "1710034065"

    controller.athlete_dao.exists.assert_called_once_with(
        mock_db_session, "dni", "1710034065"
    )
    controller.athlete_dao.create.assert_called_once()
    controller.statistic_dao.create.assert_called_once()
    controller.person_ms_service.create_or_get_person.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_athlete_unl_duplicate_dni(
    controller, mock_db_session, valid_data
):
    """Test con DNI duplicado."""
    controller.athlete_dao.exists.return_value = True

    with pytest.raises(AlreadyExistsException) as exc:
        await controller.register_athlete_unl(mock_db_session, valid_data)

    assert "DNI" in str(exc.value)
    controller.athlete_dao.create.assert_not_called()
    controller.statistic_dao.create.assert_not_called()


@pytest.mark.asyncio
async def test_register_athlete_unl_invalid_dni(
    controller, mock_db_session, valid_data
):
    """Test con DNI inválido."""
    with pytest.raises(ValidationError):
        AthleteInscriptionDTO(
            first_name=valid_data.first_name,
            last_name=valid_data.last_name,
            dni="invalid",
            phone=valid_data.phone,
            birth_date=valid_data.birth_date,
            weight=valid_data.weight,
            height=valid_data.height,
        )


@pytest.mark.asyncio
async def test_register_athlete_unl_invalid_date(
    controller, mock_db_session, valid_data
):
    """Test con fecha de nacimiento inválida."""
    controller.athlete_dao.exists.return_value = False

    with pytest.raises(ValidationError):
        AthleteInscriptionDTO(
            first_name=valid_data.first_name,
            last_name=valid_data.last_name,
            dni=valid_data.dni,
            phone=valid_data.phone,
            birth_date="invalid-date",
            weight=valid_data.weight,
            height=valid_data.height,
        )
