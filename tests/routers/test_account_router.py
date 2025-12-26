from unittest.mock import MagicMock, patch

import pytest

from app.utils.exceptions import UnauthorizedException


@pytest.mark.asyncio
async def test_login_success(client):
    """Prueba de login exitoso."""
    with patch("app.services.routers.account_router.account_controller") as mock_ctrl:
        mock_resp = MagicMock()
        mock_resp.model_dump.return_value = {
            "access_token": "token123",
            "token_type": "bearer",
            "expires_in": 3600,
        }
        mock_ctrl.login.return_value = mock_resp

        response = await client.post(
            "/api/v1/accounts/login",
            json={"email": "user@test.com", "password": "Password123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["access_token"] == "token123"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Prueba de login con credenciales inválidas."""
    with patch("app.services.routers.account_router.account_controller") as mock_ctrl:
        mock_ctrl.login.side_effect = UnauthorizedException("Credenciales inválidas")

        response = await client.post(
            "/api/v1/accounts/login",
            json={"email": "user@test.com", "password": "WrongPass!"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Credenciales inválidas" in data["detail"]


@pytest.mark.asyncio
async def test_password_reset_request_success(client):
    """Prueba de solicitud de restablecimiento de contraseña con respuesta genérica."""
    with patch("app.services.routers.account_router.account_controller") as mock_ctrl:
        mock_ctrl.request_password_reset.return_value = None

        response = await client.post(
            "/api/v1/accounts/password-reset/request",
            json={"email": "user@test.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"] is None


@pytest.mark.asyncio
async def test_password_reset_request_always_generic_success(client):
    """Siempre responde éxito genérico para evitar enumeración de cuentas."""
    with patch("app.services.routers.account_router.account_controller") as mock_ctrl:
        mock_ctrl.request_password_reset.return_value = None

        response = await client.post(
            "/api/v1/accounts/password-reset/request",
            json={"email": "missing@test.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"] is None


@pytest.mark.asyncio
async def test_password_reset_confirm_success(client):
    """Prueba de confirmación de restablecimiento de contraseña exitoso."""
    with patch("app.services.routers.account_router.account_controller") as mock_ctrl:
        mock_ctrl.confirm_password_reset.return_value = None

        response = await client.post(
            "/api/v1/accounts/password-reset/confirm",
            json={"token": "reset123", "new_password": "NewPass123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Contraseña actualizada" in data["message"]


@pytest.mark.asyncio
async def test_password_reset_confirm_invalid_token(client):
    """Prueba de confirmación de restablecimiento de contraseña con token inválido."""
    with patch("app.services.routers.account_router.account_controller") as mock_ctrl:
        mock_ctrl.confirm_password_reset.side_effect = UnauthorizedException(
            "Token inválido o expirado"
        )

        response = await client.post(
            "/api/v1/accounts/password-reset/confirm",
            json={"token": "badtoken", "new_password": "NewPass123!"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Token inválido" in data["detail"]


@pytest.mark.asyncio
async def test_login_validation_error(client):
    """Debe responder 422 si falla la validación de entrada."""

    response = await client.post(
        "/api/v1/accounts/login",
        json={"email": "bad-email", "password": "short"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_password_reset_confirm_unexpected_error(client):
    """Debe responder 500 ante error inesperado del controlador."""

    with patch("app.services.routers.account_router.account_controller") as mock_ctrl:
        mock_ctrl.confirm_password_reset.side_effect = Exception("boom")

        response = await client.post(
            "/api/v1/accounts/password-reset/confirm",
            json={"token": "reset123", "new_password": "NewPass123!"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "Error inesperado" in data["detail"]
