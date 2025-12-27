# tests/controllers/test_user_controller.py
"""
Tests unitarios para UserController.

Cubre:
- admin_create_user: crear administrador/entrenador
- admin_update_user: actualizar usuario existente
- get_all_users: listar usuarios con filtros
- get_user_by_id: obtener detalle de usuario
- desactivate_user: desactivar usuario (soft delete)
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.controllers.user_controller import UserController
from app.models.enums.rol import Role
from app.schemas.user_schema import AdminCreateUserRequest, AdminUpdateUserRequest
from app.utils.exceptions import AlreadyExistsException, ValidationException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def user_controller():
    """Instancia del controlador con mocks inyectados."""
    controller = UserController()
    controller.person_ms_service = MagicMock()
    controller.person_ms_service.create_or_get_person = AsyncMock()
    controller.person_ms_service.update_person = AsyncMock()
    controller.person_ms_service.get_user_by_identification = AsyncMock()
    return controller


@pytest.fixture
def valid_create_payload():
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


@pytest.fixture
def valid_update_payload():
    """Payload válido para actualizar un usuario."""
    return AdminUpdateUserRequest(
        first_name="Juan Carlos",
        last_name="Pérez López",
        direction="Av. Nueva 456",
        phone="0999888777",
        type_identification="CEDULA",
        type_stament="EXTERNOS",
    )


@pytest.fixture
def mock_user():
    """Usuario mock con cuenta asociada."""
    user = MagicMock()
    user.id = 1
    user.full_name = "Juan Pérez"
    user.dni = "0926687856"
    user.external = "12345678-1234-1234-1234-123456789012"
    user.is_active = True
    user.created_at = datetime.now()
    user.updated_at = None
    user.account = MagicMock()
    user.account.id = 10
    user.account.email = "juan.perez@example.com"
    user.account.role = Role.ADMINISTRATOR
    return user


# ==============================================
# TESTS: admin_create_user
# ==============================================


@pytest.mark.asyncio
async def test_admin_create_user_success_administrator(
    user_controller, mock_db_session, valid_create_payload
):
    """Crear administrador exitosamente."""
    # Arrange
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(
        return_value=MagicMock(id=1, full_name="Juan Pérez", dni="0926687856")
    )
    user_controller.account_dao.create = MagicMock(
        return_value=MagicMock(id=10, role=Role.ADMINISTRATOR)
    )
    user_controller.person_ms_service.create_or_get_person.return_value = (
        "12345678-1234-1234-1234-123456789012"
    )

    # Act
    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_create_payload
    )

    # Assert
    assert result.id == 1
    assert result.account_id == 10
    assert result.full_name == "Juan Pérez"
    assert result.email == "juan.perez@example.com"
    assert result.role in ["ADMINISTRATOR", "Administrator"]
    assert result.external == "12345678-1234-1234-1234-123456789012"

    user_controller.person_ms_service.create_or_get_person.assert_called_once()
    user_controller.user_dao.create.assert_called_once()
    user_controller.account_dao.create.assert_called_once()


@pytest.mark.asyncio
async def test_admin_create_user_success_coach(
    user_controller, mock_db_session, valid_create_payload
):
    """Crear entrenador exitosamente."""
    # Arrange
    valid_create_payload.role = Role.COACH
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=False)
    user_controller.user_dao.create = MagicMock(return_value=MagicMock(id=2))
    user_controller.account_dao.create = MagicMock(
        return_value=MagicMock(id=20, role=Role.COACH)
    )
    user_controller.person_ms_service.create_or_get_person.return_value = (
        "22345678-1234-1234-1234-123456789012"
    )

    # Act
    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_create_payload
    )

    # Assert
    assert result.role in ["COACH", "Coach"]


@pytest.mark.asyncio
async def test_admin_create_user_dni_duplicado(
    user_controller, mock_db_session, valid_create_payload
):
    """Debe lanzar excepción si el DNI ya existe localmente."""
    # Arrange
    user_controller.user_dao.exists = MagicMock(return_value=True)

    # Act & Assert
    with pytest.raises(
        AlreadyExistsException, match="Ya existe un usuario con ese DNI"
    ):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_create_payload
        )

    user_controller.person_ms_service.create_or_get_person.assert_not_called()


@pytest.mark.asyncio
async def test_admin_create_user_email_duplicado(
    user_controller, mock_db_session, valid_create_payload
):
    """Debe lanzar excepción si el email ya existe localmente."""
    # Arrange
    user_controller.user_dao.exists = MagicMock(return_value=False)
    user_controller.account_dao.exists = MagicMock(return_value=True)

    # Act & Assert
    with pytest.raises(
        AlreadyExistsException, match="Ya existe una cuenta con ese email"
    ):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_create_payload
        )

    user_controller.person_ms_service.create_or_get_person.assert_not_called()


def test_admin_create_user_rol_invalido():
    """Debe rechazar roles no válidos en la validación del schema."""
    with pytest.raises(ValidationError):
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role="deportista",  # Rol inválido
            direction="Calle 123",
            phone="0987654321",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )


def test_admin_create_user_dni_corto():
    """Debe rechazar DNI con menos de 10 dígitos."""
    with pytest.raises(ValidationError):
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="123456789",  # Solo 9 dígitos
            password="SecurePass123",
            role="administrator",
            direction="Calle 123",
            phone="0987654321",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )


def test_admin_create_user_password_corto():
    """Debe rechazar password con menos de 8 caracteres."""
    with pytest.raises(ValidationError):
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="Pass12",  # Solo 6 caracteres
            role="administrator",
            direction="Calle 123",
            phone="0987654321",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )


# ==============================================
# TESTS: admin_update_user
# ==============================================


@pytest.mark.asyncio
async def test_admin_update_user_success(
    user_controller, mock_db_session, valid_update_payload, mock_user
):
    """Actualizar usuario exitosamente."""
    # Arrange
    user_controller.user_dao.get_by_id = MagicMock(return_value=mock_user)
    user_controller.person_ms_service.update_person.return_value = (
        "new-external-12345678901234567890123456"
    )

    updated_user = MagicMock()
    updated_user.id = 1
    updated_user.full_name = "Juan Carlos Pérez López"
    updated_user.external = "new-external-12345678901234567890123456"
    updated_user.updated_at = datetime.now()
    updated_user.is_active = True
    updated_user.account = mock_user.account

    user_controller.user_dao.update = MagicMock(return_value=updated_user)

    # Act
    result = await user_controller.admin_update_user(
        db=mock_db_session, payload=valid_update_payload, user_id=1
    )

    # Assert
    assert result.id == 1
    assert result.full_name == "Juan Carlos Pérez López"
    assert result.is_active is True
    user_controller.user_dao.update.assert_called_once()


@pytest.mark.asyncio
async def test_admin_update_user_not_found(
    user_controller, mock_db_session, valid_update_payload
):
    """Debe lanzar excepción si el usuario no existe."""
    # Arrange
    user_controller.user_dao.get_by_id = MagicMock(return_value=None)

    # Act & Assert
    with pytest.raises(ValidationException, match="El usuario a actualizar no existe"):
        await user_controller.admin_update_user(
            db=mock_db_session, payload=valid_update_payload, user_id=999
        )


@pytest.mark.asyncio
async def test_admin_update_user_sync_external(
    user_controller, mock_db_session, valid_update_payload, mock_user
):
    """Debe sincronizar el external si el MS lo cambia."""
    # Arrange
    new_external = "NEW-EXTERNAL-123456789012345678901234567890"

    user_controller.user_dao.get_by_id = MagicMock(return_value=mock_user)
    user_controller.person_ms_service.update_person.return_value = new_external

    updated_user = MagicMock()
    updated_user.id = 1
    updated_user.full_name = "Juan Carlos Pérez López"
    updated_user.external = new_external
    updated_user.updated_at = datetime.now()
    updated_user.is_active = True
    updated_user.account = mock_user.account

    user_controller.user_dao.update = MagicMock(return_value=updated_user)

    # Act
    await user_controller.admin_update_user(
        db=mock_db_session, payload=valid_update_payload, user_id=1
    )

    # Assert - verificar que se llamó update con el nuevo external
    call_args = user_controller.user_dao.update.call_args
    update_data = call_args[0][2]
    assert update_data["external"] == new_external


# ==============================================
# TESTS: get_all_users
# ==============================================


def test_get_all_users_returns_list(user_controller, mock_db_session):
    """Debe retornar lista de usuarios con total."""
    # Arrange
    from app.schemas.user_schema import UserFilter

    mock_users = [MagicMock(), MagicMock()]
    user_controller.user_dao.get_all_with_filters = MagicMock(
        return_value=(mock_users, 2)
    )

    filters = UserFilter(page=1, limit=10)

    # Act
    items, total = user_controller.get_all_users(db=mock_db_session, filters=filters)

    # Assert
    assert len(items) == 2
    assert total == 2
    user_controller.user_dao.get_all_with_filters.assert_called_once()


def test_get_all_users_with_search_filter(user_controller, mock_db_session):
    """Debe aplicar filtro de búsqueda."""
    # Arrange
    from app.schemas.user_schema import UserFilter

    user_controller.user_dao.get_all_with_filters = MagicMock(return_value=([], 0))
    filters = UserFilter(page=1, limit=10, search="Juan")

    # Act
    user_controller.get_all_users(db=mock_db_session, filters=filters)

    # Assert
    call_args = user_controller.user_dao.get_all_with_filters.call_args
    assert call_args[1]["filters"].search == "Juan"


def test_get_all_users_with_role_filter(user_controller, mock_db_session):
    """Debe aplicar filtro de rol."""
    # Arrange
    from app.schemas.user_schema import UserFilter

    user_controller.user_dao.get_all_with_filters = MagicMock(return_value=([], 0))
    filters = UserFilter(page=1, limit=10, role="Administrator")

    # Act
    user_controller.get_all_users(db=mock_db_session, filters=filters)

    # Assert
    call_args = user_controller.user_dao.get_all_with_filters.call_args
    assert call_args[1]["filters"].role == "Administrator"


# ==============================================
# TESTS: get_user_by_id
# ==============================================


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_controller, mock_db_session, mock_user):
    """Debe retornar detalle del usuario con datos del MS."""
    # Arrange
    user_controller.user_dao.get_by_id = MagicMock(return_value=mock_user)
    user_controller.person_ms_service.get_user_by_identification.return_value = {
        "status": "success",
        "data": {
            "external": mock_user.external,
            "identification": mock_user.dni,
            "firts_name": "Juan",
            "last_name": "Pérez",
            "direction": "Calle Principal 123",
            "phono": "0987654321",
            "type_identification": "CEDULA",
            "type_stament": "DOCENTES",
        },
    }

    # Act
    result = await user_controller.get_user_by_id(db=mock_db_session, user_id=1)

    # Assert
    assert result is not None
    assert result.id == 1
    assert result.first_name == "Juan"
    assert result.last_name == "Pérez"
    assert result.dni == mock_user.dni
    assert result.email == mock_user.account.email


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_controller, mock_db_session):
    """Debe retornar None si el usuario no existe."""
    # Arrange
    user_controller.user_dao.get_by_id = MagicMock(return_value=None)

    # Act
    result = await user_controller.get_user_by_id(db=mock_db_session, user_id=999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_id_ms_error(user_controller, mock_db_session, mock_user):
    """Debe lanzar excepción si el MS no retorna datos."""
    # Arrange
    user_controller.user_dao.get_by_id = MagicMock(return_value=mock_user)
    user_controller.person_ms_service.get_user_by_identification.return_value = None

    # Act & Assert
    with pytest.raises(
        ValidationException, match="No se encontró la información de la persona"
    ):
        await user_controller.get_user_by_id(db=mock_db_session, user_id=1)


# ==============================================
# TESTS: desactivate_user
# ==============================================


def test_desactivate_user_success(user_controller, mock_db_session, mock_user):
    """Debe desactivar usuario correctamente."""
    # Arrange
    user_controller.user_dao.get_by_id = MagicMock(return_value=mock_user)
    user_controller.user_dao.update = MagicMock(return_value=mock_user)

    # Act
    user_controller.desactivate_user(db=mock_db_session, user_id=1)

    # Assert
    user_controller.user_dao.update.assert_called_once_with(
        mock_db_session, 1, {"is_active": False}
    )


def test_desactivate_user_not_found(user_controller, mock_db_session):
    """Debe lanzar excepción si el usuario no existe."""
    # Arrange
    user_controller.user_dao.get_by_id = MagicMock(return_value=None)

    # Act & Assert
    with pytest.raises(ValidationException, match="El usuario a desactivar no existe"):
        user_controller.desactivate_user(db=mock_db_session, user_id=999)


# ==============================================
# TESTS: Validación de schemas
# ==============================================


def test_type_identification_normalizes_dni_to_cedula():
    """type_identification debe normalizar 'dni' a 'CEDULA'."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="0926687856",
        password="SecurePass123",
        role="administrator",
        type_identification="dni",
        type_stament="externos",
    )
    assert payload.type_identification == "CEDULA"


def test_type_stament_normalizes_to_uppercase():
    """type_stament debe normalizarse a mayúsculas."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="0926687856",
        password="SecurePass123",
        role="coach",
        type_identification="CEDULA",
        type_stament="externos",
    )
    assert payload.type_stament == "EXTERNOS"


def test_role_accepts_spanish_names():
    """role debe aceptar nombres en español."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="0926687856",
        password="SecurePass123",
        role="administrador",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )
    assert payload.role == Role.ADMINISTRATOR


def test_role_accepts_entrenador():
    """role debe aceptar 'entrenador' como Coach."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="0926687856",
        password="SecurePass123",
        role="entrenador",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )
    assert payload.role == Role.COACH
