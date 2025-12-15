# tests/controllers/test_user_controller.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.controllers.user_controller import UserController
from app.schemas.user_schema import AdminCreateUserRequest
from app.models.enums.rol import Role
from app.utils.exceptions import ValidationException, AlreadyExistsException

@pytest.fixture
def user_controller():
    """Instancia del controlador con mocks inyectados."""
    controller = UserController()
    controller.person_client = AsyncMock()
    return controller

@pytest.fixture
def valid_payload():
    """Payload válido para crear un admin."""
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
async def test_admin_create_user_success_administrator(user_controller, mock_db_session, valid_payload):
    """Crear administrador exitosamente."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(return_value=MagicMock(
        id=1,
        external_person_id="abc-123-uuid",
        full_name="Juan Pérez",
        dni="0926687856"
    ))
    user_controller.account_dao.create = MagicMock(return_value=MagicMock(
        id=10,
        external_account_id="abc-123-uuid",
        role=Role.ADMINISTRATOR
    ))

    user_controller.person_client.create_person_with_account.return_value = {
        "status": "success",
        "message": "Se ha registrado correctamente",
        "data": {},
        "errors": []
    }

    user_controller.person_client.get_by_identification.return_value = {
        "data": {
            "external_id": "abc-123-uuid",
            "external": "abc-123-uuid",
            "name": "Juan",
            "last_name": "Pérez",
            "identification": "0926687856",
        }
    }

    result = await user_controller.admin_create_user(
        db=mock_db_session,
        payload=valid_payload,
        requester_account_id=None
    )

    assert result.user_id == 1
    assert result.account_id == 10
    assert result.external_person_id == "abc-123-uuid"
    assert result.full_name == "Juan Pérez"
    assert result.email == "juan.perez@example.com"
    # Ajustar según el .value real de tu enum
    assert result.role in ["ADMINISTRATOR", "Administrator"]

    user_controller.person_client.create_person_with_account.assert_called_once()
    user_controller.user_dao.create.assert_called_once()
    user_controller.account_dao.create.assert_called_once()


@pytest.mark.asyncio
async def test_admin_create_user_success_coach(user_controller, mock_db_session, valid_payload):
    """Crear entrenador exitosamente."""
    valid_payload.role = "coach"
    
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(return_value=MagicMock(id=2))
    user_controller.account_dao.create = MagicMock(return_value=MagicMock(
        id=20,
        role=Role.COACH
    ))

    user_controller.person_client.create_person_with_account.return_value = {
        "status": "success",
        "message": "Se ha registrado correctamente",
    }
    user_controller.person_client.get_by_identification.return_value = {
        "data": {"external_id": "def-456-uuid", "external": "def-456-uuid"}
    }

    result = await user_controller.admin_create_user(
        db=mock_db_session,
        payload=valid_payload
    )

    assert result.role in ["COACH", "Coach"]


@pytest.mark.asyncio
async def test_admin_create_user_dni_duplicado(user_controller, mock_db_session, valid_payload):
    """Debe lanzar excepción si el DNI ya existe localmente."""
    user_controller.user_dao.exists = MagicMock(return_value=True)

    with pytest.raises(AlreadyExistsException, match="Ya existe un usuario con ese DNI"):
        await user_controller.admin_create_user(
            db=mock_db_session,
            payload=valid_payload
        )

    user_controller.person_client.create_person_with_account.assert_not_called()


@pytest.mark.asyncio
async def test_admin_create_user_rol_invalido(user_controller, mock_db_session, valid_payload):
    """Debe rechazar roles no válidos."""
    valid_payload.role = "deportista"
    user_controller.user_dao.exists = MagicMock(return_value=False)

    with pytest.raises(ValidationException) as exc_info:
        await user_controller.admin_create_user(
            db=mock_db_session,
            payload=valid_payload
        )
    
    assert "Rol inválido" in str(exc_info.value)


@pytest.mark.asyncio
async def test_admin_create_user_error_ms_usuarios(user_controller, mock_db_session, valid_payload):
    """Debe manejar error del MS de usuarios al crear persona."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock()
    user_controller.account_dao.create = MagicMock()
    
    user_controller.person_client.create_person_with_account.side_effect = Exception("Connection timeout")

    with pytest.raises(ValidationException) as exc_info:
        await user_controller.admin_create_user(
            db=mock_db_session,
            payload=valid_payload
        )
    
    assert "No se pudo registrar la persona" in str(exc_info.value)
    user_controller.user_dao.create.assert_not_called()
    user_controller.account_dao.create.assert_not_called()


@pytest.mark.asyncio
async def test_admin_create_user_ms_responde_error(user_controller, mock_db_session, valid_payload):
    """Debe manejar respuesta de error del MS de usuarios."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    
    user_controller.person_client.create_person_with_account.return_value = {
        "status": "error",
        "message": "Email ya existe en el sistema",
    }

    with pytest.raises(ValidationException) as exc_info:
        await user_controller.admin_create_user(
            db=mock_db_session,
            payload=valid_payload
        )
    
    assert "Error desde MS de usuarios" in str(exc_info.value)


@pytest.mark.asyncio
async def test_admin_create_user_sin_external_id(user_controller, mock_db_session, valid_payload):
    """Debe fallar si el MS no devuelve external_id."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    
    user_controller.person_client.create_person_with_account.return_value = {
        "status": "success"
    }
    user_controller.person_client.get_by_identification.return_value = {
        "data": {}
    }

    with pytest.raises(ValidationException) as exc_info:
        await user_controller.admin_create_user(
            db=mock_db_session,
            payload=valid_payload
        )
    
    assert "no devolvió external_id" in str(exc_info.value)
