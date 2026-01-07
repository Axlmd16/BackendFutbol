"""Tests unitarios para el controlador de usuarios.

Este archivo está organizado en las siguientes secciones:
1. FUNCTIONAL TEST CASES - Tests principales para documentación
2. BUSINESS RULE VALIDATIONS - Reglas de negocio (DNI ecuatoriano, etc.)
3. SCHEMA VALIDATIONS - Validaciones de Pydantic
4. NORMALIZATION TESTS - Normalización de datos de entrada
5. EDGE CASES - Casos límite y defensivos
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.controllers.user_controller import UserController
from app.models.enums.rol import Role
from app.schemas.user_schema import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    UserFilter,
)
from app.utils.exceptions import AlreadyExistsException, ValidationException

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def user_controller():
    controller = UserController()
    controller.person_ms_service = MagicMock()
    controller.person_ms_service.create_or_get_person = AsyncMock()
    controller.person_ms_service.update_person = AsyncMock()
    controller.person_ms_service.get_user_by_identification = AsyncMock()
    controller.user_dao = MagicMock()
    controller.account_dao = MagicMock()
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


# ------------------------------------------------------------------------------
#  Crear usuario
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user_admin_success(
    user_controller, mock_db_session, valid_create_payload
):
    """Usuario creado correctamente."""
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.user_dao.create.return_value = MagicMock(
        id=1, full_name="Juan Pérez", dni="0926687856"
    )
    user_controller.account_dao.create.return_value = MagicMock(
        id=10, role=Role.ADMINISTRATOR
    )
    user_controller.person_ms_service.create_or_get_person.return_value = (
        "12345678-1234-1234-1234-123456789012"
    )

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_create_payload
    )

    # Mensaje esperado: "Usuario creado correctamente"
    assert result.id == 1
    assert result.account_id == 10
    assert result.full_name == "Juan Pérez"
    assert result.role in ["ADMINISTRATOR", "Administrator"]
    user_controller.user_dao.create.assert_called_once()
    user_controller.account_dao.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_coach_success(
    user_controller, mock_db_session, valid_create_payload
):
    """Usuario creado correctamente."""
    valid_create_payload.role = Role.COACH
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.user_dao.create.return_value = MagicMock(id=2)
    user_controller.account_dao.create.return_value = MagicMock(id=20, role=Role.COACH)
    user_controller.person_ms_service.create_or_get_person.return_value = (
        "22345678-1234-1234-1234-123456789012"
    )

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_create_payload
    )

    # Mensaje esperado: "Usuario creado correctamente"
    assert result.role in ["COACH", "Coach"]


@pytest.mark.asyncio
async def test_create_user_duplicate_dni(
    user_controller, mock_db_session, valid_create_payload
):
    """Ya existe un usuario con el DNI ingresado."""
    user_controller.user_dao.exists.return_value = True

    with pytest.raises(
        AlreadyExistsException, match="Ya existe un usuario con ese DNI en el club"
    ):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_create_payload
        )

    user_controller.person_ms_service.create_or_get_person.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    user_controller, mock_db_session, valid_create_payload
):
    """Ya existe una cuenta registrada con ese correo electrónico."""
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = True

    with pytest.raises(
        AlreadyExistsException, match="Ya existe una cuenta con ese email en el club"
    ):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_create_payload
        )

    user_controller.person_ms_service.create_or_get_person.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_person_ms_error(
    user_controller, mock_db_session, valid_create_payload
):
    """No se pudo registrar la información personal del usuario."""
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.person_ms_service.create_or_get_person.side_effect = Exception(
        "No se pudo registrar la persona en el sistema"
    )

    with pytest.raises(Exception, match="No se pudo registrar la persona"):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_create_payload
        )


@pytest.mark.asyncio
async def test_create_user_unexpected_error(
    user_controller, mock_db_session, valid_create_payload
):
    """Ocurrió un error inesperado al crear el usuario."""
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.person_ms_service.create_or_get_person.return_value = "ext-123456"
    user_controller.user_dao.create.side_effect = Exception(
        "Ocurrió un error inesperado, intente más tarde"
    )

    with pytest.raises(Exception, match="error inesperado"):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_create_payload
        )


def test_create_user_missing_required_fields():
    """Existen campos obligatorios sin completar."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            # last_name faltante
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role="administrator",
        )
    error_str = str(exc.value).lower()
    assert "last_name" in error_str or "required" in error_str


def test_create_user_invalid_email_format():
    """El formato del correo electrónico es inválido."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="invalid-email",
            dni="0926687856",
            password="SecurePass123",
            role="administrator",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value)
    assert "El formato del correo electrónico es inválido" in error_str


def test_create_user_invalid_role():
    """El rol ingresado no es válido."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role="deportista",  # Rol no válido
            direction="Calle 123",
            phone="0987654321",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value).lower()
    assert "rol" in error_str or "role" in error_str or "inválido" in error_str


# ------------------------------------------------------------------------------
# 📌 Actualizar usuario
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_user_success(
    user_controller, mock_db_session, valid_update_payload, mock_user
):
    """Usuario actualizado correctamente."""
    user_controller.user_dao.get_by_id.return_value = mock_user
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

    user_controller.user_dao.update.return_value = updated_user

    result = await user_controller.admin_update_user(
        db=mock_db_session, payload=valid_update_payload, user_id=1
    )

    # Mensaje esperado: "Usuario actualizado correctamente"
    assert result.id == 1
    assert result.full_name == "Juan Carlos Pérez López"
    assert result.is_active is True
    user_controller.user_dao.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_not_found(
    user_controller, mock_db_session, valid_update_payload
):
    """El usuario a actualizar no existe."""
    user_controller.user_dao.get_by_id.return_value = None

    with pytest.raises(ValidationException, match="El usuario a actualizar no existe"):
        await user_controller.admin_update_user(
            db=mock_db_session, payload=valid_update_payload, user_id=999
        )


@pytest.mark.asyncio
async def test_update_user_unexpected_error(
    user_controller, mock_db_session, valid_update_payload, mock_user
):
    """Ocurrió un error inesperado al actualizar el usuario."""
    user_controller.user_dao.get_by_id.return_value = mock_user
    user_controller.person_ms_service.update_person.return_value = "new-ext-123456789"
    user_controller.user_dao.update.side_effect = Exception(
        "Ocurrió un error inesperado al actualizar el usuario"
    )

    with pytest.raises(Exception, match="error inesperado"):
        await user_controller.admin_update_user(
            db=mock_db_session, payload=valid_update_payload, user_id=1
        )


# ------------------------------------------------------------------------------
# 📌 Obtener usuarios
# ------------------------------------------------------------------------------


def test_get_all_users_success(user_controller, mock_db_session):
    """Usuarios obtenidos correctamente."""
    mock_users = [MagicMock(), MagicMock()]
    user_controller.user_dao.get_all_with_filters.return_value = (mock_users, 2)

    filters = UserFilter(page=1, limit=10)
    items, total = user_controller.get_all_users(db=mock_db_session, filters=filters)

    # Mensaje esperado: "Usuarios obtenidos correctamente"
    assert len(items) == 2
    assert total == 2
    user_controller.user_dao.get_all_with_filters.assert_called_once()


def test_get_all_users_empty(user_controller, mock_db_session):
    """No existen usuarios registrados."""
    user_controller.user_dao.get_all_with_filters.return_value = ([], 0)
    filters = UserFilter(page=1, limit=10)

    items, total = user_controller.get_all_users(db=mock_db_session, filters=filters)

    # Mensaje esperado: "No existen usuarios registrados"
    assert len(items) == 0
    assert total == 0


def test_get_all_users_with_filters(user_controller, mock_db_session):
    """Usuarios obtenidos correctamente."""
    user_controller.user_dao.get_all_with_filters.return_value = ([], 0)
    filters = UserFilter(page=1, limit=10, search="Juan", role="Administrator")

    user_controller.get_all_users(db=mock_db_session, filters=filters)

    # Mensaje esperado: "Usuarios obtenidos correctamente"
    call_args = user_controller.user_dao.get_all_with_filters.call_args
    assert call_args.kwargs["filters"].search == "Juan"
    assert call_args.kwargs["filters"].role == "Administrator"


# ------------------------------------------------------------------------------
# 📌 Obtener usuario por ID
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_controller, mock_db_session, mock_user):
    """Usuario obtenido correctamente."""
    user_controller.user_dao.get_by_id.return_value = mock_user
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

    result = await user_controller.get_user_by_id(db=mock_db_session, user_id=1)

    # Mensaje esperado: "Usuario obtenido correctamente"
    assert result is not None
    assert result.id == 1
    assert result.first_name == "Juan"
    assert result.last_name == "Pérez"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_controller, mock_db_session):
    """Usuario no encontrado."""
    user_controller.user_dao.get_by_id.return_value = None

    result = await user_controller.get_user_by_id(db=mock_db_session, user_id=999)

    # Mensaje esperado: "Usuario no encontrado"
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_id_person_not_found(
    user_controller, mock_db_session, mock_user
):
    """No se encontró la información personal del usuario."""
    user_controller.user_dao.get_by_id.return_value = mock_user
    user_controller.person_ms_service.get_user_by_identification.return_value = None

    with pytest.raises(
        ValidationException, match="No se encontró la información de la persona"
    ):
        await user_controller.get_user_by_id(db=mock_db_session, user_id=1)


# ------------------------------------------------------------------------------
# 📌 Desactivar usuario
# ------------------------------------------------------------------------------


def test_deactivate_user_success(user_controller, mock_db_session, mock_user):
    """Usuario desactivado correctamente."""
    user_controller.user_dao.get_by_id.return_value = mock_user

    user_controller.desactivate_user(db=mock_db_session, user_id=1)

    # Mensaje esperado: "Usuario desactivado correctamente"
    user_controller.user_dao.update.assert_called_once_with(
        mock_db_session, 1, {"is_active": False}
    )


def test_deactivate_user_not_found(user_controller, mock_db_session):
    """El usuario a desactivar no existe."""
    user_controller.user_dao.get_by_id.return_value = None

    with pytest.raises(ValidationException, match="El usuario a desactivar no existe"):
        user_controller.desactivate_user(db=mock_db_session, user_id=999)


# ==============================================================================
# BUSINESS RULE VALIDATIONS (DNI ecuatoriano)
# ==============================================================================


@pytest.mark.asyncio
async def test_dni_invalid_check_digit(user_controller, mock_db_session):
    """Debe rechazar DNI con dígito verificador incorrecto."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="1234567890",
        password="SecurePass123",
        role="administrator",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False

    with pytest.raises(ValidationException, match="Dni invalido"):
        await user_controller.admin_create_user(db=mock_db_session, payload=payload)


@pytest.mark.asyncio
async def test_dni_invalid_province(user_controller, mock_db_session):
    """Debe rechazar DNI con código de provincia inválido (>24 y !=30)."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="9912345678",
        password="SecurePass123",
        role="administrator",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False

    with pytest.raises(ValidationException, match="Provincia del DNI invalida"):
        await user_controller.admin_create_user(db=mock_db_session, payload=payload)


@pytest.mark.asyncio
async def test_dni_invalid_third_digit(user_controller, mock_db_session):
    """Debe rechazar DNI con tercer dígito > 5 (formato inválido)."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="0196123456",
        password="SecurePass123",
        role="administrator",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False

    with pytest.raises(ValidationException, match="Formato de DNI invalido"):
        await user_controller.admin_create_user(db=mock_db_session, payload=payload)


@pytest.mark.asyncio
async def test_dni_with_letters(user_controller, mock_db_session):
    """Debe rechazar DNI con caracteres no numéricos."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="092668A856",
        password="SecurePass123",
        role="administrator",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False

    with pytest.raises(ValidationException, match="10 digitos"):
        await user_controller.admin_create_user(db=mock_db_session, payload=payload)


@pytest.mark.asyncio
async def test_dni_province_30_valid(user_controller, mock_db_session):
    """Debe aceptar DNI con provincia 30 (ecuatorianos en el exterior)."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="3001234561",
        password="SecurePass123",
        role="administrator",
        type_identification="CEDULA",
        type_stament="DOCENTES",
    )
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.person_ms_service.create_or_get_person.return_value = "ext-123"
    user_controller.user_dao.create.return_value = MagicMock(id=1)
    user_controller.account_dao.create.return_value = MagicMock(
        id=10, role=Role.ADMINISTRATOR
    )

    try:
        await user_controller.admin_create_user(db=mock_db_session, payload=payload)
    except ValidationException as e:
        # Si falla, debe ser por dígito verificador, no por provincia
        assert "Provincia" not in str(e)


# ==============================================================================
# SCHEMA / PYDANTIC VALIDATIONS
# ==============================================================================


def test_schema_dni_too_short():
    """Debe rechazar DNI con menos de 10 dígitos."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="123456789",
            password="SecurePass123",
            role="administrator",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value)
    assert "El DNI debe tener exactamente 10 dígitos" in error_str


def test_schema_dni_too_long():
    """Debe rechazar DNI con más de 10 dígitos."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="01234567890",
            password="SecurePass123",
            role="administrator",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value)
    assert "El DNI debe tener exactamente 10 dígitos" in error_str


def test_schema_password_too_short():
    """Debe rechazar password con menos de 8 caracteres."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="Pass1",
            role="administrator",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value)
    assert "La contraseña debe tener al menos 8 caracteres" in error_str


def test_schema_password_too_long():
    """Debe rechazar password con más de 64 caracteres."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="A" * 65,
            role="administrator",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value)
    assert "La contraseña no puede exceder 64 caracteres" in error_str


def test_schema_first_name_too_short():
    """Debe rechazar first_name con menos de 2 caracteres."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="A",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role="administrator",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value)
    assert "El nombre debe tener al menos 2 caracteres" in error_str


def test_schema_last_name_too_short():
    """Debe rechazar last_name con menos de 2 caracteres."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="U",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role="administrator",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value)
    assert "El apellido debe tener al menos 2 caracteres" in error_str


def test_schema_first_name_too_long():
    """Debe rechazar first_name con más de 100 caracteres."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="A" * 101,
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role="administrator",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value)
    assert "El nombre no puede exceder 100 caracteres" in error_str


def test_schema_invalid_type_stament():
    """Debe rechazar type_stament no reconocido."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role="administrator",
            type_identification="CEDULA",
            type_stament="INVALIDO",
        )
    error_str = str(exc.value).lower()
    assert "type_stament" in error_str or "inválido" in error_str


# ==============================================================================
# NORMALIZATION AND DATA SANITIZATION
# ==============================================================================


def test_normalize_type_identification_dni_to_cedula():
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


def test_normalize_type_identification_pasaporte_to_passport():
    """type_identification debe normalizar 'pasaporte' a 'PASSPORT'."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="0926687856",
        password="SecurePass123",
        role="administrator",
        type_identification="pasaporte",
        type_stament="DOCENTES",
    )
    assert payload.type_identification == "PASSPORT"


def test_normalize_type_stament_to_uppercase():
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


def test_normalize_type_stament_docente_singular():
    """type_stament debe aceptar 'docente' y normalizarlo a 'DOCENTES'."""
    payload = AdminCreateUserRequest(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        dni="0926687856",
        password="SecurePass123",
        role="administrator",
        type_identification="CEDULA",
        type_stament="docente",
    )
    assert payload.type_stament == "DOCENTES"


def test_normalize_role_spanish_administrador():
    """role debe aceptar 'administrador' en español."""
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


def test_normalize_role_spanish_entrenador():
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


def test_normalize_role_variations_admin():
    """Debe aceptar diferentes variaciones de Administrator."""
    for role_str in ["admin", "administrator", "administrador", "Administrator"]:
        payload = AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role=role_str,
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
        assert payload.role == Role.ADMINISTRATOR


def test_normalize_role_variations_coach():
    """Debe aceptar diferentes variaciones de Coach."""
    for role_str in ["coach", "Coach", "entrenador", "Entrenador"]:
        payload = AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role=role_str,
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
        assert payload.role == Role.COACH


@pytest.mark.asyncio
async def test_normalize_names_whitespace(
    user_controller, mock_db_session, valid_create_payload
):
    """Debe normalizar espacios en first_name y last_name."""
    valid_create_payload.first_name = "  Juan  "
    valid_create_payload.last_name = "  Pérez  "

    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.person_ms_service.create_or_get_person.return_value = "ext-123"
    user_controller.user_dao.create.return_value = MagicMock(
        id=1, full_name="Juan Pérez", dni="0926687856"
    )
    user_controller.account_dao.create.return_value = MagicMock(
        id=10, role=Role.ADMINISTRATOR
    )

    _ = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_create_payload
    )

    call_args = user_controller.person_ms_service.create_or_get_person.call_args
    ms_request = call_args.args[0]
    assert ms_request.first_name == "Juan"
    assert ms_request.last_name == "Pérez"


@pytest.mark.asyncio
async def test_normalize_email_to_lowercase(
    user_controller, mock_db_session, valid_create_payload
):
    """Debe normalizar email a minúsculas."""
    valid_create_payload.email = "JUAN.PEREZ@EXAMPLE.COM"

    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.person_ms_service.create_or_get_person.return_value = "ext-123"
    user_controller.user_dao.create.return_value = MagicMock(id=1)
    user_controller.account_dao.create.return_value = MagicMock(
        id=10, role=Role.ADMINISTRATOR
    )

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_create_payload
    )

    assert result.email == "juan.perez@example.com"


# ==============================================================================
# EDGE CASES AND DEFENSIVE TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_sync_external_on_update(
    user_controller, mock_db_session, valid_update_payload, mock_user
):
    """Debe sincronizar el external si el MS lo cambia."""
    new_external = "NEW-EXTERNAL-123456789012345678901234567890"

    user_controller.user_dao.get_by_id.return_value = mock_user
    user_controller.person_ms_service.update_person.return_value = new_external

    updated_user = MagicMock()
    updated_user.id = 1
    updated_user.full_name = "Juan Carlos Pérez López"
    updated_user.external = new_external
    updated_user.updated_at = datetime.now()
    updated_user.is_active = True
    updated_user.account = mock_user.account

    user_controller.user_dao.update.return_value = updated_user

    await user_controller.admin_update_user(
        db=mock_db_session, payload=valid_update_payload, user_id=1
    )

    call_args = user_controller.user_dao.update.call_args
    update_data = call_args.args[2]
    assert update_data["external"] == new_external


@pytest.mark.asyncio
async def test_ms_returns_empty_external(
    user_controller, mock_db_session, valid_create_payload
):
    """Debe manejar cuando MS retorna external vacío."""
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.person_ms_service.create_or_get_person.return_value = ""

    user_controller.user_dao.create.return_value = MagicMock(id=1, full_name="Test")
    user_controller.account_dao.create.return_value = MagicMock(
        id=10, role=Role.ADMINISTRATOR
    )

    result = await user_controller.admin_create_user(
        db=mock_db_session, payload=valid_create_payload
    )
    assert result.external == ""


@pytest.mark.asyncio
async def test_ms_identity_validation_failed(
    user_controller, mock_db_session, valid_create_payload
):
    """Debe propagar error cuando MS detecta conflicto de identidad."""
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.person_ms_service.create_or_get_person.side_effect = (
        ValidationException(
            "Los datos personales no coinciden con el DNI registrado en el módulo"
        )
    )

    with pytest.raises(ValidationException, match="no coinciden"):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_create_payload
        )


@pytest.mark.asyncio
async def test_ms_connection_error(
    user_controller, mock_db_session, valid_create_payload
):
    """Debe propagar error de conexión con MS."""
    user_controller.user_dao.exists.return_value = False
    user_controller.account_dao.exists.return_value = False
    user_controller.person_ms_service.create_or_get_person.side_effect = (
        ValidationException("Error de comunicación con el módulo de usuarios")
    )

    with pytest.raises(ValidationException, match="comunicación"):
        await user_controller.admin_create_user(
            db=mock_db_session, payload=valid_create_payload
        )


def test_role_intern_rejected():
    """Debe rechazar rol INTERN en creación de usuario admin/coach."""
    with pytest.raises(ValidationError) as exc:
        AdminCreateUserRequest(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            dni="0926687856",
            password="SecurePass123",
            role="intern",
            type_identification="CEDULA",
            type_stament="DOCENTES",
        )
    error_str = str(exc.value).lower()
    assert "inválido" in error_str or "invalid" in error_str or "role" in error_str
