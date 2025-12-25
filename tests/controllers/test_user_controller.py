# tests/controllers/test_user_controller.py
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.controllers.user_controller import UserController
from app.models.enums.rol import Role
from app.schemas.user_schema import AdminCreateUserRequest, AdminUpdateUserRequest
from app.utils.exceptions import AlreadyExistsException, ValidationException


@pytest.fixture
def user_controller():
    """Instancia del controlador con mocks inyectados."""
    controller = UserController()
    # Mockear el person_client DENTRO del person_ms_service
    controller.person_ms_service.person_client = AsyncMock()
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
async def test_admin_create_user_success_administrator(
    user_controller, mock_db_session, valid_payload
):
    """Crear administrador exitosamente."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(
        return_value=MagicMock(
            id=1,
            full_name="Juan Pérez",
            dni="0926687856",
        )
    )
    user_controller.account_dao.create = MagicMock(
        return_value=MagicMock(id=10, role=Role.ADMINISTRATOR)
    )

    user_controller.person_ms_service.person_client.create_person_with_account.return_value = {
        "status": "success",
        "message": "Se ha registrado correctamente",
        "data": {"external": "12345678-1234-1234-1234-123456789012"},
        "errors": [],
    }

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_payload
    )

    assert result.user_id == 1
    assert result.account_id == 10
    assert result.full_name == "Juan Pérez"
    assert result.email == "juan.perez@example.com"
    assert result.role in ["ADMINISTRATOR", "Administrator"]

    user_controller.person_ms_service.person_client.create_person_with_account.assert_called_once()
    user_controller.user_dao.create.assert_called_once()
    user_controller.account_dao.create.assert_called_once()


@pytest.mark.asyncio
async def test_admin_create_user_success_coach(
    user_controller, mock_db_session, valid_payload
):
    """Crear entrenador exitosamente."""
    valid_payload.role = "coach"

    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(return_value=MagicMock(id=2))
    user_controller.account_dao.create = MagicMock(
        return_value=MagicMock(id=20, role=Role.COACH)
    )

    user_controller.person_ms_service.person_client.create_person_with_account.return_value = {
        "status": "success",
        "message": "Se ha registrado correctamente",
        "data": {"external": "22345678-1234-1234-1234-123456789012"},
    }

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_payload
    )

    assert result.role in ["COACH", "Coach"]


@pytest.mark.asyncio
async def test_admin_create_user_dni_duplicado(
    user_controller, mock_db_session, valid_payload
):
    """Debe lanzar excepción si el DNI ya existe localmente."""
    user_controller.user_dao.exists = MagicMock(return_value=True)

    # No debería llamar al MS porque falla validación local primero
    with pytest.raises(
        AlreadyExistsException, match="Ya existe un usuario con ese DNI"
    ):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )

    user_controller.person_ms_service.person_client.create_person_with_account.assert_not_called()


@pytest.mark.asyncio
async def test_admin_create_user_rol_invalido(
    user_controller, mock_db_session, valid_payload
):
    """Debe rechazar roles no válidos."""
    with pytest.raises(ValidationError):
        valid_payload.role = "deportista"


@pytest.mark.asyncio
async def test_admin_create_user_error_ms_usuarios(
    user_controller, mock_db_session, valid_payload
):
    """Debe manejar error del MS de usuarios al crear persona."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.person_ms_service.person_client.create_person_with_account.side_effect = Exception(
        "Connection timeout"
    )

    with pytest.raises(ValidationException) as exc_info:
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )

    assert "Error de comunicación con el módulo de usuarios" in str(exc_info.value)


@pytest.mark.asyncio
async def test_admin_create_user_ms_responde_error(
    user_controller, mock_db_session, valid_payload
):
    """Debe manejar respuesta de error del MS de usuarios."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.person_ms_service.person_client.create_person_with_account.return_value = {
        "status": "error",
        "message": "Error interno del servidor",
    }

    with pytest.raises(ValidationException) as exc_info:
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )

    assert "Error interno del servidor" in str(exc_info.value)


@pytest.mark.asyncio
async def test_admin_create_user_email_duplicado(
    user_controller, mock_db_session, valid_payload
):
    """Debe lanzar excepción si el email ya existe localmente."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=True)

    # No debería llamar al MS porque falla validación local primero
    with pytest.raises(
        AlreadyExistsException, match="Ya existe una cuenta con ese email"
    ):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )

    user_controller.person_ms_service.person_client.create_person_with_account.assert_not_called()


@pytest.mark.asyncio
async def test_admin_create_user_persona_existe_en_otro_club(
    user_controller, mock_db_session, valid_payload
):
    """Si la persona existe en MS (otro club) pero no localmente, debe continuar."""
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(return_value=MagicMock(id=3))
    user_controller.account_dao.create = MagicMock(
        return_value=MagicMock(id=30, role=Role.ADMINISTRATOR)
    )

    # MS responde que ya existe (persona de otro club)
    user_controller.person_ms_service.person_client.create_person_with_account.return_value = {
        "status": "error",
        "message": "Ya existe una persona con esa identificación",
    }

    # El controlador debe recuperar el external por DNI para enlazar localmente
    user_controller.person_ms_service.person_client.get_by_identification.return_value = {
        "status": "success",
        "data": {
            "external": "32345678-1234-1234-1234-123456789012",
            "first_name": "Juan",
            "last_name": "Pérez",
        },
    }

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_payload
    )

    # Debe crear el usuario local aunque ya exista en MS
    assert result.user_id == 3
    assert result.account_id == 30
    user_controller.user_dao.create.assert_called_once()
    user_controller.account_dao.create.assert_called_once()


@pytest.mark.asyncio
async def test_admin_create_user_persona_existe_nombre_no_coincide_debe_fallar(
    user_controller, mock_db_session, valid_payload
):
    """Si el DNI existe en el MS pero los nombres no coinciden, debe rechazar."""

    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)

    # MS responde que ya existe
    user_controller.person_ms_service.person_client.create_person_with_account.return_value = {
        "status": "error",
        "message": "Ya existe una persona con esa identificación",
    }

    # En el MS el DNI pertenece a otra persona
    user_controller.person_ms_service.person_client.get_by_identification.return_value = {
        "status": "success",
        "data": {
            "external": "42345678-1234-1234-1234-123456789012",
            "first_name": "Juan",
            "last_name": "Pérez",
        },
    }

    # Pero aquí intentamos registrar con nombres distintos
    valid_payload.first_name = "Domenica"
    valid_payload.last_name = "Riofrío"

    with pytest.raises(ValidationException) as exc_info:
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_payload
        )

    assert "DNI ya está registrado" in str(exc_info.value) or "DNI ya está" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_admin_update_user_actualiza_external_local(
    user_controller, mock_db_session
):
    """Si el MS cambia el external al actualizar, debe sincronizarse en el club."""

    payload = AdminUpdateUserRequest(
        id=1,
        first_name="Juan",
        last_name="Pérez",
        direction="Calle Principal 123",
        phone="0987654321",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )

    local_external = "OLD-EXTERNAL-123456789012345678901234567890"

    user_controller.user_dao.get_by_id = MagicMock(
        return_value=MagicMock(
            id=1,
            full_name="Juan Pérez",
            external=local_external,
            dni="0926687856",
            updated_at=MagicMock(),
            is_active=True,
            account=MagicMock(email="juan.perez@example.com", role=Role.ADMINISTRATOR),
        )
    )

    # MS actualiza y devuelve nuevo external (o se recupera por DNI)
    user_controller.person_ms_service.person_client.update_person.return_value = {
        "status": "success",
        "data": {"external": "NEW-EXTERNAL-123456789012345678901234567890"},
    }

    user_controller.user_dao.update = MagicMock(
        return_value=MagicMock(
            id=1,
            full_name="Juan Pérez",
            external="NEW-EXTERNAL-123456789012345678901234567890",
            updated_at=MagicMock(),
            is_active=True,
            account=MagicMock(email="juan.perez@example.com", role=Role.ADMINISTRATOR),
        )
    )

    result = await user_controller.admin_update_user(
        db=mock_db_session, payload=payload
    )

    # Debe llamar al MS usando el external LOCAL, no el que venga del frontend.
    called_payload = (
        user_controller.person_ms_service.person_client.update_person.call_args.args[0]
    )
    assert called_payload["external"] == local_external

    # Verifica que se haya persistido el external nuevo localmente
    user_controller.user_dao.update.assert_called_once()
    _, _, update_data = user_controller.user_dao.update.mock_calls[0].args
    assert update_data["external"] == "NEW-EXTERNAL-123456789012345678901234567890"
    assert result.user_id == 1
