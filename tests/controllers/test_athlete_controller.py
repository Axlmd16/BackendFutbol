from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.schemas.athlete_schema import (
    AthleteInscriptionDTO,
    MinorAthleteDataDTO,
)
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


# ==================== TESTS PARA MENORES DE EDAD ====================


@pytest.mark.asyncio
async def test_minor_athlete_valid_age_5_years():
    """Test: Atleta menor de 5 años (edad mínima válida)."""
    today = date.today()
    birth_date = today.replace(year=today.year - 5)

    athlete_data = MinorAthleteDataDTO(
        first_name="María",
        last_name="González",
        dni="1234567890",
        birth_date=birth_date,
        sex="FEMALE",
        height=1.10,
        weight=20.0,
    )

    assert athlete_data.first_name == "María"
    assert athlete_data.birth_date == birth_date


@pytest.mark.asyncio
async def test_minor_athlete_valid_age_17_years():
    """Test: Atleta de 17 años (edad máxima válida para menores)."""
    today = date.today()
    birth_date = today - timedelta(days=17 * 365 + 180)

    athlete_data = MinorAthleteDataDTO(
        first_name="Carlos",
        last_name="Rodríguez",
        dni="0987654321",
        birth_date=birth_date,
        sex="MALE",
        height=1.75,
        weight=65.0,
    )

    assert athlete_data.first_name == "Carlos"


@pytest.mark.asyncio
async def test_minor_athlete_invalid_age_4_years():
    """Test: Rechazar atleta de 4 años (muy joven)."""
    today = date.today()
    birth_date = today.replace(year=today.year - 4)

    with pytest.raises(ValidationError) as exc_info:
        MinorAthleteDataDTO(
            first_name="Niño",
            last_name="Muy Joven",
            dni="1111111111",
            birth_date=birth_date,
            sex="MALE",
            height=1.00,
            weight=15.0,
        )

    errors = exc_info.value.errors()
    assert len(errors) > 0
    error_msg = errors[0]["msg"]
    print(f"\nValidacion correcta: {error_msg}")
    assert (
        "debe tener al menos 5 años" in error_msg
    ), f"Mensaje de error incorrecto: {error_msg}"


@pytest.mark.asyncio
async def test_minor_athlete_invalid_age_18_years():
    """Test: Rechazar atleta de 18 años (mayor de edad)."""
    today = date.today()
    birth_date = today.replace(year=today.year - 18)

    with pytest.raises(ValidationError) as exc_info:
        MinorAthleteDataDTO(
            first_name="Mayor",
            last_name="De Edad",
            dni="2222222222",
            birth_date=birth_date,
            sex="MALE",
            height=1.75,
            weight=70.0,
        )

    errors = exc_info.value.errors()
    assert len(errors) > 0
    error_msg = errors[0]["msg"]
    print(f"\nValidacion correcta: {error_msg}")
    assert (
        "debe ser menor de 18 años" in error_msg
    ), f"Mensaje de error incorrecto: {error_msg}"


@pytest.mark.asyncio
async def test_minor_athlete_boundary_turns_18_tomorrow():
    """Test: Atleta cumple 18 años mañana (aún es válido hoy)."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    birth_date = date(
        year=tomorrow.year - 18, month=tomorrow.month, day=tomorrow.day
    )

    athlete_data = MinorAthleteDataDTO(
        first_name="Casi",
        last_name="Mayor",
        dni="3333333333",
        birth_date=birth_date,
        sex="FEMALE",
        height=1.65,
        weight=55.0,
    )

    assert athlete_data.first_name == "Casi"


@pytest.mark.asyncio
async def test_minor_athlete_invalid_future_date():
    """Test: Rechazar fecha de nacimiento en el futuro."""
    today = date.today()
    birth_date = today + timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        MinorAthleteDataDTO(
            first_name="Del",
            last_name="Futuro",
            dni="4444444444",
            birth_date=birth_date,
            sex="MALE",
            height=1.50,
            weight=40.0,
        )

    errors = exc_info.value.errors()
    assert len(errors) > 0
    error_msg = errors[0]["msg"]
    print(f"\nValidacion correcta: {error_msg}")
    assert (
        "no puede ser en el futuro" in error_msg
    ), f"Mensaje de error incorrecto: {error_msg}"
