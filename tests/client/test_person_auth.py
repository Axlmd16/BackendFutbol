"""Tests para PersonAuthService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.client.person_auth import PersonAuthService


class TestPersonAuthServiceInit:
    """Tests para inicialización de PersonAuthService."""

    def test_init_token_none(self):
        """Token inicial es None."""
        service = PersonAuthService()
        assert service._token is None

    def test_token_property(self):
        """Propiedad token retorna el valor interno."""
        service = PersonAuthService()
        assert service.token is None

        service._token = "test_token"
        assert service.token == "test_token"


class TestPersonAuthServiceLogin:
    """Tests para método login."""

    @pytest.fixture
    def service(self):
        """Servicio para tests."""
        return PersonAuthService()

    @pytest.mark.asyncio
    @patch("app.client.person_auth.settings")
    @patch("app.client.person_auth.httpx.AsyncClient")
    async def test_login_success(self, mock_async_client_class, mock_settings, service):
        """Login exitoso guarda el token."""
        # Configurar settings
        mock_settings.PERSON_MS_ADMIN_EMAIL = "admin@test.com"
        mock_settings.PERSON_MS_ADMIN_PASSWORD = "password123"
        mock_settings.PERSON_MS_BASE_URL = "http://localhost:8001"

        # Configurar respuesta del cliente
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"token": "Bearer jwt_token_123"}}
        mock_response.raise_for_status = MagicMock()

        # Configurar cliente async
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        # Ejecutar login
        result = await service.login()

        # Verificar
        assert result == "Bearer jwt_token_123"
        assert service._token == "Bearer jwt_token_123"
        assert service.token == "Bearer jwt_token_123"

    @pytest.mark.asyncio
    @patch("app.client.person_auth.settings")
    @patch("app.client.person_auth.httpx.AsyncClient")
    async def test_login_calls_correct_endpoint(
        self, mock_async_client_class, mock_settings, service
    ):
        """Login llama al endpoint correcto."""
        mock_settings.PERSON_MS_ADMIN_EMAIL = "admin@test.com"
        mock_settings.PERSON_MS_ADMIN_PASSWORD = "secret"
        mock_settings.PERSON_MS_BASE_URL = "http://localhost:8001"

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"token": "token123"}}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        await service.login()

        # Verificar que se llama con los datos correctos
        mock_client.post.assert_called_once_with(
            "/api/person/login", json={"email": "admin@test.com", "password": "secret"}
        )

    @pytest.mark.asyncio
    @patch("app.client.person_auth.settings")
    @patch("app.client.person_auth.httpx.AsyncClient")
    async def test_login_uses_base_url(
        self, mock_async_client_class, mock_settings, service
    ):
        """Login usa la URL base correcta."""
        mock_settings.PERSON_MS_BASE_URL = "https://api.example.com"
        mock_settings.PERSON_MS_ADMIN_EMAIL = "user@test.com"
        mock_settings.PERSON_MS_ADMIN_PASSWORD = "pass"

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"token": "token"}}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        await service.login()

        mock_async_client_class.assert_called_once_with(
            base_url="https://api.example.com"
        )

    @pytest.mark.asyncio
    @patch("app.client.person_auth.settings")
    @patch("app.client.person_auth.httpx.AsyncClient")
    async def test_login_raises_on_http_error(
        self, mock_async_client_class, mock_settings, service
    ):
        """Login propaga errores HTTP."""
        import httpx

        mock_settings.PERSON_MS_BASE_URL = "http://localhost:8001"
        mock_settings.PERSON_MS_ADMIN_EMAIL = "admin@test.com"
        mock_settings.PERSON_MS_ADMIN_PASSWORD = "wrong_password"

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="401 Unauthorized", request=MagicMock(), response=MagicMock()
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPStatusError):
            await service.login()

        # Token no se debe guardar en caso de error
        assert service._token is None

    @pytest.mark.asyncio
    @patch("app.client.person_auth.settings")
    @patch("app.client.person_auth.httpx.AsyncClient")
    async def test_login_overwrites_existing_token(
        self, mock_async_client_class, mock_settings, service
    ):
        """Login sobrescribe token existente."""
        # Establecer token previo
        service._token = "old_token"

        mock_settings.PERSON_MS_BASE_URL = "http://localhost:8001"
        mock_settings.PERSON_MS_ADMIN_EMAIL = "admin@test.com"
        mock_settings.PERSON_MS_ADMIN_PASSWORD = "password"

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"token": "new_token"}}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client_class.return_value = mock_client

        result = await service.login()

        assert result == "new_token"
        assert service._token == "new_token"
        assert service.token == "new_token"
