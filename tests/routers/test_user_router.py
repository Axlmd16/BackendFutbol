"""Pruebas del router de usuarios."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.exceptions import AlreadyExistsException, ValidationException


@pytest.fixture
def mock_person_client():
    with patch("app.controllers.user_controller.PersonClient") as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.mark.asyncio
async def test_admin_create_user_endpoint_success(client, mock_person_client):
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_result = MagicMock(
            user_id=5,
            account_id=50,
            external_person_id="test-uuid-123",
            external_account_id="test-uuid-123",
            full_name="Ana López",
            email="ana.lopez@test.com",
            role="ADMINISTRATOR",
        )
        mock_result.model_dump = MagicMock(
            return_value={
                "user_id": 5,
                "account_id": 50,
                "external_person_id": "test-uuid-123",
                "external_account_id": "test-uuid-123",
                "full_name": "Ana López",
                "email": "ana.lopez@test.com",
                "role": "ADMINISTRATOR",
            }
        )
        mock_controller.admin_create_user = AsyncMock(return_value=mock_result)

        response = await client.post(
            "/api/v1/users/admin-create",
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
        assert data["data"]["external_person_id"] == "test-uuid-123"


@pytest.mark.asyncio
async def test_admin_create_user_endpoint_dni_invalido(client):
    response = await client.post(
        "/api/v1/users/admin-create",
        json={
            "first_name": "Carlos",
            "last_name": "Ruiz",
            "email": "carlos@test.com",
            "dni": "123",
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
    dni_errors = [e for e in data.get("errors", []) if "dni" in e["field"]]
    assert len(dni_errors) > 0


@pytest.mark.asyncio
async def test_admin_create_user_endpoint_rol_invalido(client, mock_person_client):
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_create_user = AsyncMock(
            side_effect=ValidationException("Rol inválido: deportista")
        )

        response = await client.post(
            "/api/v1/users/admin-create",
            json={
                "first_name": "Pedro",
                "last_name": "González",
                "email": "pedro@test.com",
                "dni": "0604964025",
                "password": "Password123",
                "role": "administrator",
                "direction": "Calle 456",
                "phone": "0988888888",
                "type_identification": "CEDULA",
                "type_stament": "DOCENTES",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "Rol inválido" in data["detail"]


@pytest.mark.asyncio
async def test_admin_create_user_endpoint_dni_duplicado(client, mock_person_client):
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_create_user = AsyncMock(
            side_effect=AlreadyExistsException("Ya existe un usuario con ese DNI")
        )

        response = await client.post(
            "/api/v1/users/admin-create",
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
        assert "Ya existe un usuario con ese DNI" in data["detail"]


@pytest.mark.asyncio
async def test_admin_create_user_endpoint_error_ms_usuarios(client, mock_person_client):
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_create_user = AsyncMock(
            side_effect=ValidationException(
                "No se pudo registrar la persona en el MS de usuarios"
            )
        )

        response = await client.post(
            "/api/v1/users/admin-create",
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
        assert "No se pudo registrar la persona" in data["detail"]


@pytest.mark.asyncio
async def test_admin_create_user_endpoint_rol_coach_success(client, mock_person_client):
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_result = MagicMock(
            user_id=6,
            account_id=60,
            external_person_id="test-uuid-456",
            external_account_id="test-uuid-456",
            full_name="Carlos Mendez",
            email="carlos@test.com",
            role="COACH",
        )
        mock_result.model_dump = MagicMock(
            return_value={
                "user_id": 6,
                "account_id": 60,
                "external_person_id": "test-uuid-456",
                "external_account_id": "test-uuid-456",
                "full_name": "Carlos Mendez",
                "email": "carlos@test.com",
                "role": "COACH",
            }
        )
        mock_controller.admin_create_user = AsyncMock(return_value=mock_result)

        response = await client.post(
            "/api/v1/users/admin-create",
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
async def test_admin_create_user_endpoint_error_generico(client, mock_person_client):
    with patch("app.services.routers.user_router.user_controller") as mock_controller:
        mock_controller.admin_create_user = AsyncMock(
            side_effect=Exception("Error inesperado del sistema")
        )

        response = await client.post(
            "/api/v1/users/admin-create",
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
        assert "Error inesperado" in data["detail"]


@pytest.mark.asyncio
async def test_admin_create_user_endpoint_password_corto(client):
    response = await client.post(
        "/api/v1/users/admin-create",
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
    password_errors = [e for e in data.get("errors", []) if "password" in e["field"]]
    assert len(password_errors) > 0
