"""Tests para RepresentativeController."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.controllers.representative_controller import RepresentativeController
from app.models.enums.relationship import Relationship
from app.schemas.representative_schema import (
    RelationshipType,
    RepresentativeInscriptionDTO,
)
from app.utils.exceptions import AlreadyExistsException, ValidationException


@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)


@pytest.fixture
def controller():
    c = RepresentativeController()
    # Mocks de DAOs
    c.representative_dao.exists = MagicMock()
    c.representative_dao.create = MagicMock()
    c.representative_dao.get_by_field = MagicMock()
    c.representative_dao.get_by_id = MagicMock()
    c.representative_dao.get_all_with_filters = MagicMock()
    c.representative_dao.update = MagicMock()
    # Mock de PersonMSService
    c.person_ms_service.create_or_get_person = AsyncMock(
        return_value="12345678-1234-1234-1234-123456789012"
    )
    c.person_ms_service.get_user_by_identification = AsyncMock(
        return_value={
            "data": {
                "firts_name": "Juan",
                "last_name": "Pérez",
                "direction": "Av. Principal",
                "type_identification": "CEDULA",
                "type_stament": "EXTERNOS",
            }
        }
    )
    return c


@pytest.fixture
def valid_representative_data():
    return RepresentativeInscriptionDTO(
        first_name="Juan",
        last_name="Pérez",
        dni="1710034065",
        phone="0999123456",
        email="juan@test.com",
        direction="Av. Principal 123",
        type_identification="CEDULA",
        type_stament="EXTERNOS",
        relationship_type=RelationshipType.FATHER,
    )


@pytest.mark.asyncio
async def test_create_representative_success(
    controller, mock_db_session, valid_representative_data
):
    """Test exitoso de creación de representante."""
    controller.representative_dao.exists.return_value = False
    controller.representative_dao.create.return_value = MagicMock(
        id=1,
        full_name="Juan Pérez",
        dni="1710034065",
        relationship_type=Relationship.FATHER,
    )

    result = await controller.create_representative(
        mock_db_session, valid_representative_data
    )

    assert result.representative_id == 1
    assert result.full_name == "Juan Pérez"
    assert result.dni == "1710034065"
    assert result.relationship_type == "Father"

    controller.representative_dao.exists.assert_called_once_with(
        mock_db_session, "dni", "1710034065"
    )
    controller.representative_dao.create.assert_called_once()
    controller.person_ms_service.create_or_get_person.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_representative_duplicate_dni(
    controller, mock_db_session, valid_representative_data
):
    """Test con DNI duplicado."""
    controller.representative_dao.exists.return_value = True

    with pytest.raises(AlreadyExistsException) as exc:
        await controller.create_representative(
            mock_db_session, valid_representative_data
        )

    assert "representante" in str(exc.value).lower() or "dni" in str(exc.value).lower()
    controller.representative_dao.create.assert_not_called()


def test_get_representative_by_dni_found(controller, mock_db_session):
    """Test de búsqueda por DNI encontrado."""
    mock_rep = MagicMock(
        id=1,
        full_name="Juan Pérez",
        dni="1710034065",
        phone="0999123456",
        relationship_type=Relationship.FATHER,
        is_active=True,
        created_at=MagicMock(isoformat=lambda: "2025-01-01T00:00:00"),
    )
    controller.representative_dao.get_by_field.return_value = mock_rep

    result = controller.get_representative_by_dni(mock_db_session, "1710034065")

    assert result is not None
    assert result.id == 1
    assert result.full_name == "Juan Pérez"
    assert result.dni == "1710034065"


def test_get_representative_by_dni_not_found(controller, mock_db_session):
    """Test de búsqueda por DNI no encontrado."""
    controller.representative_dao.get_by_field.return_value = None

    result = controller.get_representative_by_dni(mock_db_session, "9999999999")

    assert result is None


@pytest.mark.asyncio
async def test_get_representative_by_id_success(controller, mock_db_session):
    """Test de obtener representante por ID."""
    mock_rep = MagicMock(
        id=1,
        external_person_id="ext-123",
        full_name="Juan Pérez",
        dni="1710034065",
        phone="0999123456",
        email="juan@test.com",
        relationship_type=Relationship.FATHER,
        is_active=True,
        created_at=MagicMock(isoformat=lambda: "2025-01-01T00:00:00"),
        updated_at=None,
    )
    controller.representative_dao.get_by_id.return_value = mock_rep

    result = await controller.get_representative_by_id(mock_db_session, 1)

    assert result.id == 1
    assert result.full_name == "Juan Pérez"
    assert result.first_name == "Juan"  # Del MS


@pytest.mark.asyncio
async def test_get_representative_by_id_not_found(controller, mock_db_session):
    """Test de obtener representante por ID no encontrado."""
    controller.representative_dao.get_by_id.return_value = None

    with pytest.raises(ValidationException) as exc:
        await controller.get_representative_by_id(mock_db_session, 999)

    assert "no encontrado" in str(exc.value).lower()


def test_deactivate_representative_success(controller, mock_db_session):
    """Test de desactivación exitosa."""
    mock_rep = MagicMock(id=1)
    controller.representative_dao.get_by_id.return_value = mock_rep

    controller.deactivate_representative(mock_db_session, 1)

    controller.representative_dao.update.assert_called_once_with(
        mock_db_session, 1, {"is_active": False}
    )


def test_deactivate_representative_not_found(controller, mock_db_session):
    """Test de desactivación cuando no existe."""
    controller.representative_dao.get_by_id.return_value = None

    with pytest.raises(ValidationException) as exc:
        controller.deactivate_representative(mock_db_session, 999)

    assert "no encontrado" in str(exc.value).lower()


def test_activate_representative_success(controller, mock_db_session):
    """Test de activación exitosa."""
    mock_rep = MagicMock(id=1, is_active=False)
    controller.representative_dao.get_by_id.return_value = mock_rep

    controller.activate_representative(mock_db_session, 1)

    controller.representative_dao.update.assert_called_once_with(
        mock_db_session, 1, {"is_active": True}
    )


# Tests de validación de schema


def test_representative_dto_valid():
    """Test de DTO válido."""
    dto = RepresentativeInscriptionDTO(
        first_name="María",
        last_name="García",
        dni="1710034065",
        phone="0999123456",
        relationship_type="MOTHER",
    )
    assert dto.relationship_type == RelationshipType.MOTHER


def test_representative_dto_relationship_padre():
    """Test de relación 'PADRE' normalizada a FATHER."""
    dto = RepresentativeInscriptionDTO(
        first_name="Juan",
        last_name="Pérez",
        dni="1710034065",
        relationship_type="PADRE",
    )
    assert dto.relationship_type == RelationshipType.FATHER


def test_representative_dto_relationship_tutor():
    """Test de relación 'TUTOR' normalizada a LEGAL_GUARDIAN."""
    dto = RepresentativeInscriptionDTO(
        first_name="Ana",
        last_name="López",
        dni="1710034065",
        relationship_type="TUTOR",
    )
    assert dto.relationship_type == RelationshipType.LEGAL_GUARDIAN


def test_representative_dto_invalid_relationship():
    """Test de relación inválida."""
    with pytest.raises(ValidationError):
        RepresentativeInscriptionDTO(
            first_name="Test",
            last_name="User",
            dni="1710034065",
            relationship_type="INVALID",
        )
