"""Pruebas para el controlador de usuarios."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.controllers.user_controller import UserController
from app.models.enums.rol import Role
from app.schemas.user_schema import AdminCreateUserRequest
from app.utils.exceptions import AlreadyExistsException, ValidationException


@pytest.fixture
def user_controller():
    controller = UserController()
    controller.person_client = AsyncMock()
    return controller


@pytest.fixture
def valid_payload():
    return AdminCreateUserRequest(
        first_name="Juan",
        last_name="Pérez",
        email="juan.perez@example.com",
        dni="0926687856",
        password="SecurePass123",
        role="administrator",
        direction="Calle Principal 123",
        phone="0987654321",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )


@pytest.mark.asyncio
async def test_admin_create_user_success_administrator(
    user_controller, mock_db_session, valid_payload
):
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(return_value=MagicMock(id=1))
    user_controller.account_dao.create = MagicMock(
        return_value=MagicMock(id=10, role=Role.ADMINISTRATOR)
    )

    user_controller.person_client.create_person_with_account.return_value = {
        "status": "success",
        "message": "OK",
    }
    user_controller.person_client.get_by_identification.return_value = {
        "data": {"external": "abc-123-uuid"}
    }

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_payload
    )

    assert result.user_id == 1
    assert result.account_id == 10
    assert result.external_person_id == "abc-123-uuid"
    assert result.full_name == "Juan Pérez"
    assert result.email == "juan.perez@example.com"
    assert result.role == Role.ADMINISTRATOR.value

    user_controller.person_client.create_person_with_account.assert_called_once()
    user_controller.user_dao.create.assert_called_once()
    user_controller.account_dao.create.assert_called_once()


@pytest.mark.asyncio
async def test_admin_create_user_success_coach(
    user_controller, mock_db_session, valid_payload
):
    valid_payload.role = "coach"

    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(return_value=MagicMock(id=2))
    user_controller.account_dao.create = MagicMock(
        return_value=MagicMock(id=20, role=Role.COACH)
    )

    user_controller.person_client.create_person_with_account.return_value = {
        "status": "success",
        "message": "OK",
    }
    user_controller.person_client.get_by_identification.return_value = {
        "data": {"external": "def-456-uuid"}
    }

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_payload
    )

    assert result.role == Role.COACH.value


@pytest.mark.asyncio
async def test_admin_create_user_dni_duplicado(
    user_controller, mock_db_session, valid_payload
):
    user_controller.user_dao.exists = MagicMock(return_value=True)

    with pytest.raises(
        AlreadyExistsException, match="Ya existe un usuario con ese DNI"
    ):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )

    user_controller.person_client.create_person_with_account.assert_not_called()


@pytest.mark.asyncio
async def test_admin_create_user_rol_invalido(
    user_controller, mock_db_session, valid_payload
):
    valid_payload.role = "deportista"
    user_controller.user_dao.exists = MagicMock(return_value=False)

    with pytest.raises(ValidationException, match="Rol inválido"):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )


@pytest.mark.asyncio
async def test_admin_create_user_error_ms_usuarios(
    user_controller, mock_db_session, valid_payload
):
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock()
    user_controller.account_dao.create = MagicMock()

    user_controller.person_client.create_person_with_account.side_effect = Exception(
        "Connection timeout"
    )

    with pytest.raises(ValidationException, match="No se pudo registrar la persona"):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )

    user_controller.user_dao.create.assert_not_called()
    user_controller.account_dao.create.assert_not_called()


@pytest.mark.asyncio
async def test_admin_create_user_ms_responde_error(
    user_controller, mock_db_session, valid_payload
):
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.person_client.create_person_with_account.return_value = {
        "status": "error",
        "message": "Email ya existe en el sistema",
    }

    with pytest.raises(ValidationException, match="Error desde MS de usuarios"):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )


@pytest.mark.asyncio
async def test_admin_create_user_sin_external_id(
    user_controller, mock_db_session, valid_payload
):
    """Debe fallar si el MS no devuelve external_id."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)

    user_controller.person_client.create_person_with_account.return_value = {
        "status": "success"
    }
    user_controller.person_client.get_by_identification.return_value = {"data": {}}

    with pytest.raises(ValidationException, match="no devolvió external_id"):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )


@pytest.mark.asyncio
async def test_admin_create_user_email_duplicado(
    user_controller, mock_db_session, valid_payload
):
    """Debe lanzar excepción si el email ya existe localmente."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=True)

    with pytest.raises(
        AlreadyExistsException, match="Ya existe una cuenta con ese email"
    ):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )

    user_controller.person_client.create_person_with_account.assert_not_called()


@pytest.mark.asyncio
async def test_admin_create_user_persona_existe_en_otro_club(
    user_controller, mock_db_session, valid_payload
):
    """Si la persona existe en MS pero no localmente, debe enlazarla."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(return_value=MagicMock(id=3))
    user_controller.account_dao.create = MagicMock(
        return_value=MagicMock(id=30, role=Role.ADMINISTRATOR)
    )

    user_controller.person_client.create_person_with_account.return_value = {
        "status": "error",
        "message": "Ya existe una persona con esa identificación",
    }
    user_controller.person_client.get_by_identification.return_value = {
        "status": "success",
        "data": {"external": "32345678-1234-1234-1234-123456789012"},
    }

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_payload
    )

    assert result.user_id == 3
    assert result.account_id == 30
    user_controller.user_dao.create.assert_called_once()
    user_controller.account_dao.create.assert_called_once()