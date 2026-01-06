# tests/routers/test_user_router.py
"""
Tests de integración para los endpoints del router de usuarios.

Cubre:
- POST /users/create: Crear admin/entrenador
- PUT /users/update/{user_id}: Actualizar usuario
- GET /users/all: Listar usuarios con paginación
- GET /users/{user_id}: Obtener detalle de usuario
- PATCH /users/desactivate/{user_id}: Desactivar usuario
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def mock_person_client():
    """Mock del PersonClient para todos los tests del router."""
    with patch("app.client.person_ms_service.PersonClient") as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


# ==============================================
# TESTS: POST /users/create
# ==============================================


@pytest.mark.asyncio
async def test_create_user_success_administrator(admin_client, mock_person_client):
    """POST /users/create debe crear administrador exitosamente."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "id": 5,
            "account_id": 50,
            "full_name": "Ana López",
            "email": "ana.lopez@test.com",
            "role": "ADMINISTRATOR",
            "external": "12345678-1234-1234-1234-123456789012",
            "is_active": True,
        }
        mock_controller.admin_create_user = AsyncMock(return_value=mock_result)

        response = await admin_client.post(
            "/api/v1/users/create",
            json={
                "first_name": "Ana",
                "last_name": "López",
                "email": "ana.lopez@test.com",
                "dni": "1713175071",
                "password": "Password123!",
                "role": "administrator",
                "direction": "Av. Principal",
                "phone": "0999888777",
                "type_identification": "CEDULA",
                "type_stament": "DOCENTES",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == 5
        assert data["data"]["role"] == "ADMINISTRATOR"


@pytest.mark.asyncio
async def test_create_user_success_coach(admin_client, mock_person_client):
    """POST /users/create debe crear entrenador exitosamente."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "id": 6,
            "account_id": 60,
            "full_name": "Carlos Mendez",
            "email": "carlos@test.com",
            "role": "COACH",
            "external": "22345678-1234-1234-1234-123456789012",
            "is_active": True,
        }
        mock_controller.admin_create_user = AsyncMock(return_value=mock_result)

        response = await admin_client.post(
            "/api/v1/users/create",
            json={
                "first_name": "Carlos",
                "last_name": "Mendez",
                "email": "carlos@test.com",
                "dni": "1234567890",
                "password": "Password123!",
                "role": "coach",
                "direction": "Av. Central",
                "phone": "0988888888",
                "type_identification": "CEDULA",
                "type_stament": "DOCENTES",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["role"] == "COACH"


@pytest.mark.asyncio
async def test_create_user_validation_dni_invalid(admin_client):
    """Debe rechazar DNI que no tenga 10 dígitos."""
    response = await admin_client.post(
        "/api/v1/users/create",
        json={
            "first_name": "Carlos",
            "last_name": "Ruiz",
            "email": "carlos@test.com",
            "dni": "123",  # DNI inválido: menos de 10 dígitos
            "password": "Password123",
            "role": "coach",
            "direction": "Calle 123",
            "phone": "0999999999",
            "type_identification": "CEDULA",
            "type_stament": "DOCENTES",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "Error de validación" in data["message"]
    assert "errors" in data
    assert isinstance(data["errors"], dict)
    # Verificar que hay error sobre el campo DNI
    assert any("dni" in key for key in data["errors"].keys())


@pytest.mark.asyncio
async def test_create_user_validation_password_short(admin_client):
    """Debe rechazar password menor a 8 caracteres."""
    response = await admin_client.post(
        "/api/v1/users/create",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@test.com",
            "dni": "1234567890",
            "password": "Pass12",
            "role": "coach",
            "direction": "Calle 123",
            "phone": "0999999999",
            "type_identification": "CEDULA",
            "type_stament": "DOCENTES",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data
    assert isinstance(data["errors"], dict)
    # Verificar que hay error sobre el campo password
    assert any("password" in key for key in data["errors"].keys())


@pytest.mark.asyncio
async def test_create_user_dni_duplicate(admin_client, mock_person_client):
    """Debe rechazar DNI duplicado con código 409."""
    from app.utils.exceptions import AlreadyExistsException

    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_create_user = AsyncMock(
            side_effect=AlreadyExistsException("Ya existe un usuario con ese DNI")
        )

        response = await admin_client.post(
            "/api/v1/users/create",
            json={
                "first_name": "Luis",
                "last_name": "Martínez",
                "email": "luis@test.com",
                "dni": "1104678770",
                "password": "Password123",
                "role": "coach",
                "direction": "Calle 789",
                "phone": "0977777777",
                "type_identification": "CEDULA",
                "type_stament": "DOCENTES",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert data["status"] == "error"
        assert "Ya existe un usuario con ese DNI" in data["message"]


@pytest.mark.asyncio
async def test_create_user_email_duplicate(admin_client, mock_person_client):
    """Debe rechazar email duplicado con código 409."""
    from app.utils.exceptions import AlreadyExistsException

    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_create_user = AsyncMock(
            side_effect=AlreadyExistsException("Ya existe una cuenta con ese email")
        )

        response = await admin_client.post(
            "/api/v1/users/create",
            json={
                "first_name": "María",
                "last_name": "García",
                "email": "duplicado@test.com",
                "dni": "1715732843",
                "password": "Password123",
                "role": "administrator",
                "direction": "Calle 101",
                "phone": "0966666666",
                "type_identification": "CEDULA",
                "type_stament": "DOCENTES",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert data["status"] == "error"
        assert "Ya existe una cuenta con ese email" in data["message"]


@pytest.mark.asyncio
async def test_create_user_ms_error(admin_client, mock_person_client):
    """Debe manejar error del MS de usuarios."""
    from app.utils.exceptions import ValidationException

    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_create_user = AsyncMock(
            side_effect=ValidationException(
                "No se pudo registrar la persona en el MS de usuarios"
            )
        )

        response = await admin_client.post(
            "/api/v1/users/create",
            json={
                "first_name": "María",
                "last_name": "Fernández",
                "email": "maria@test.com",
                "dni": "1715732843",
                "password": "Password123",
                "role": "administrator",
                "direction": "Calle 101",
                "phone": "0966666666",
                "type_identification": "CEDULA",
                "type_stament": "DOCENTES",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"
        assert "No se pudo registrar la persona" in data["message"]


@pytest.mark.asyncio
async def test_create_user_generic_error(admin_client, mock_person_client):
    """Debe manejar errores genéricos con status 500."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_create_user = AsyncMock(
            side_effect=Exception("Error inesperado del sistema")
        )

        response = await admin_client.post(
            "/api/v1/users/create",
            json={
                "first_name": "Roberto",
                "last_name": "Silva",
                "email": "roberto@test.com",
                "dni": "9876543210",
                "password": "Password123",
                "role": "administrator",
                "direction": "Calle 202",
                "phone": "0955555555",
                "type_identification": "CEDULA",
                "type_stament": "DOCENTES",
            },
        )

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "Error inesperado" in data["message"]


# ==============================================
# TESTS: PUT /users/update/{user_id}
# ==============================================


@pytest.mark.asyncio
async def test_update_user_success(admin_client, mock_person_client):
    """PUT /users/update/{user_id} debe actualizar usuario exitosamente."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "id": 1,
            "full_name": "Juan Carlos Pérez López",
            "email": "juan.perez@test.com",
            "role": "ADMINISTRATOR",
            "is_active": True,
        }

        mock_controller.admin_update_user = AsyncMock(return_value=mock_result)

        response = await admin_client.put(
            "/api/v1/users/update/1",
            json={
                "first_name": "Juan Carlos",
                "last_name": "Pérez López",
                "direction": "Nueva Dirección 456",
                "phone": "0988777666",
                "type_identification": "CEDULA",
                "type_stament": "EXTERNOS",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Usuario actualizado correctamente"
        assert data["data"]["full_name"] == "Juan Carlos Pérez López"


@pytest.mark.asyncio
async def test_update_user_not_found(admin_client, mock_person_client):
    """Debe retornar 422 si el usuario a actualizar no existe."""
    from app.utils.exceptions import ValidationException

    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_update_user = AsyncMock(
            side_effect=ValidationException("El usuario a actualizar no existe")
        )

        response = await admin_client.put(
            "/api/v1/users/update/999",
            json={
                "first_name": "Test",
                "last_name": "User",
                "direction": "Calle 123",
                "phone": "0999999999",
                "type_identification": "CEDULA",
                "type_stament": "EXTERNOS",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"
        assert "El usuario a actualizar no existe" in data["message"]


@pytest.mark.asyncio
async def test_update_user_generic_error(admin_client, mock_person_client):
    """PUT /users/update/{user_id} debe manejar errores inesperados."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_update_user = AsyncMock(
            side_effect=Exception("Error de base de datos")
        )

        response = await admin_client.put(
            "/api/v1/users/update/1",
            json={
                "first_name": "Test",
                "last_name": "User",
                "direction": "Calle 123",
                "phone": "0999999999",
                "type_identification": "CEDULA",
                "type_stament": "EXTERNOS",
            },
        )

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "Error inesperado" in data["message"]


# ==============================================
# TESTS: GET /users/all
# ==============================================


@pytest.mark.asyncio
async def test_get_all_users_success(admin_client):
    """GET /users/all debe devolver lista paginada de usuarios."""
    from app.schemas.user_schema import UserResponse

    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        # Crear objetos UserResponse válidos en lugar de MagicMock
        mock_users = [
            UserResponse(
                id=1,
                external="b82fa112-954c-4a48-812f-5fb0cb62f170",
                full_name="Juan Pérez",
                dni="1150696951",
                email="juan.perez@test.com",
                role="ADMINISTRATOR",
                is_active=True,
            ),
            UserResponse(
                id=2,
                external="c93gb223-065d-5b59-923g-6gc1dc73g281",
                full_name="María García",
                dni="0987654321",
                email="maria@test.com",
                role="COACH",
                is_active=True,
            ),
        ]
        mock_controller.get_all_users.return_value = (mock_users, 2)

        response = await admin_client.get("/api/v1/users/all")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Usuarios obtenidos correctamente"
        assert "data" in data
        assert "items" in data["data"]
        assert data["data"]["total"] == 2


@pytest.mark.asyncio
async def test_get_all_users_empty(admin_client):
    """GET /users/all debe retornar lista vacía si no hay usuarios."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.get_all_users.return_value = ([], 0)

        response = await admin_client.get("/api/v1/users/all")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_get_all_users_with_filters(admin_client):
    """GET /users/all debe aplicar filtros de búsqueda y rol."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.get_all_users.return_value = ([], 0)

        response = await admin_client.get(
            "/api/v1/users/all?search=Juan&role=Administrator&page=1&limit=10"
        )

        assert response.status_code == 200

        # Verificar que se llamó con los filtros correctos
        call_args = mock_controller.get_all_users.call_args
        filters = call_args.kwargs["filters"]
        assert filters.search == "Juan"
        assert filters.role == "Administrator"
        assert filters.page == 1
        assert filters.limit == 10


# ==============================================
# TESTS: GET /users/{user_id}
# ==============================================


@pytest.mark.asyncio
async def test_get_user_by_id_success(admin_client, mock_person_client):
    """GET /users/{user_id} debe retornar detalle del usuario."""
    from datetime import datetime

    from app.schemas.user_schema import UserDetailResponse

    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        # Crear objeto UserDetailResponse válido
        mock_result = UserDetailResponse(
            id=1,
            external="b82fa112-954c-4a48-812f-5fb0cb62f170",
            full_name="Juan Pérez",
            dni="1150696951",
            email="juan.perez@test.com",
            role="ADMINISTRATOR",
            is_active=True,
            first_name="Juan",
            last_name="Pérez",
            direction="Calle Principal 123",
            phone="0987654321",
            type_identification="CEDULA",
            type_stament="DOCENTES",
            created_at=datetime.now(),
            updated_at=None,
        )

        mock_controller.get_user_by_id = AsyncMock(return_value=mock_result)

        response = await admin_client.get("/api/v1/users/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Usuario obtenido correctamente"
        assert data["data"]["id"] == 1
        assert data["data"]["first_name"] == "Juan"
        assert data["data"]["last_name"] == "Pérez"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(admin_client, mock_person_client):
    """GET /users/{user_id} debe retornar 404 si no existe."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.get_user_by_id = AsyncMock(return_value=None)

        response = await admin_client.get("/api/v1/users/999")

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["message"] == "Usuario no encontrado"


# ==============================================
# TESTS: PATCH /users/desactivate/{user_id}
# ==============================================


@pytest.mark.asyncio
async def test_desactivate_user_success(admin_client, mock_person_client):
    """PATCH /users/desactivate/{user_id} debe desactivar usuario."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.desactivate_user = MagicMock(return_value=None)

        response = await admin_client.patch("/api/v1/users/desactivate/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Usuario desactivado correctamente"
        assert data["data"] is None


@pytest.mark.asyncio
async def test_desactivate_user_not_found(admin_client, mock_person_client):
    """PATCH /users/desactivate/{user_id} debe fallar si no existe."""
    from app.utils.exceptions import ValidationException

    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.desactivate_user = MagicMock(
            side_effect=ValidationException("El usuario a desactivar no existe")
        )

        response = await admin_client.patch("/api/v1/users/desactivate/999")

        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"
        assert "El usuario a desactivar no existe" in data["message"]


# ==============================================
# TESTS: Validación de schemas
# ==============================================


@pytest.mark.asyncio
async def test_create_user_missing_required_fields(admin_client):
    """Debe rechazar request sin campos requeridos."""
    response = await admin_client.post(
        "/api/v1/users/create",
        json={
            "first_name": "Test",
            # Faltan: last_name, email, dni, password, role
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data


@pytest.mark.asyncio
async def test_create_user_invalid_email_format(admin_client):
    """Debe rechazar email con formato inválido."""
    response = await admin_client.post(
        "/api/v1/users/create",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "invalid-email",  # Email inválido
            "dni": "1234567890",
            "password": "Password123",
            "role": "coach",
            "direction": "Calle 123",
            "phone": "0999999999",
            "type_identification": "CEDULA",
            "type_stament": "DOCENTES",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data


@pytest.mark.asyncio
async def test_create_user_normalizes_type_identification(
    admin_client, mock_person_client
):
    """Debe normalizar 'dni' a 'CEDULA' en type_identification."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"id": 1}

        mock_controller.admin_create_user = AsyncMock(return_value=mock_result)

        await admin_client.post(
            "/api/v1/users/create",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "dni": "1234567890",
                "password": "Password123",
                "role": "coach",
                "direction": "Calle 123",
                "phone": "0999999999",
                "type_identification": "dni",  # Debe normalizarse a CEDULA
                "type_stament": "externos",  # Debe normalizarse a EXTERNOS
            },
        )

        # Verificar que el controller recibió los valores normalizados
        call_args = mock_controller.admin_create_user.call_args
        payload = call_args.kwargs["payload"]
        assert payload.type_identification == "CEDULA"
        assert payload.type_stament == "EXTERNOS"


@pytest.mark.asyncio
async def test_create_user_accepts_spanish_role_names(admin_client, mock_person_client):
    """Debe aceptar nombres de rol en español."""
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"id": 1, "role": "ADMINISTRATOR"}

        mock_controller.admin_create_user = AsyncMock(return_value=mock_result)

        response = await admin_client.post(
            "/api/v1/users/create",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "dni": "1234567890",
                "password": "Password123",
                "role": "administrador",  # Rol en español
                "direction": "Calle 123",
                "phone": "0999999999",
                "type_identification": "CEDULA",
                "type_stament": "DOCENTES",
            },
        )

        assert response.status_code == 201
