"""Tests para el cliente de personas (PersonClient)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.client.person_client import PersonClient
from app.utils.exceptions import ExternalServiceException, ValidationException


class TestPersonClientInit:
    """Tests para la inicialización de PersonClient."""

    def test_init_with_defaults(self):
        """Verifica la inicialización con valores por defecto."""
        client = PersonClient()
        assert client.base_url is not None
        assert client.timeout == 10.0

    def test_init_with_custom_values(self):
        """Verifica la inicialización con valores personalizados."""
        client = PersonClient(base_url="http://custom.url", timeout=30.0)
        assert client.base_url == "http://custom.url"
        assert client.timeout == 30.0


class TestAuthorizedRequest:
    """Tests para _authorized_request."""

    @pytest.fixture
    def client(self):
        """Cliente de test."""
        return PersonClient(base_url="http://test.local")

    @pytest.mark.asyncio
    async def test_authorized_request_success(self, client):
        """Verifica una petición exitosa."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "test_token"
            mock_request.return_value = mock_response

            result = await client._authorized_request("GET", "/test")
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_authorized_request_401_retries(self, client):
        """Verifica que reintenta con nuevo token en 401."""
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": "success"}

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "old_token"
            mock_auth.login = AsyncMock(return_value="new_token")
            mock_request.side_effect = [mock_response_401, mock_response_200]

            result = await client._authorized_request("GET", "/test")
            assert result == {"data": "success"}
            mock_auth.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_authorized_request_connection_error(self, client):
        """Verifica manejo de error de conexión."""
        with patch("app.client.person_client.auth_service") as mock_auth:
            mock_auth.token = None
            mock_auth.login = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            with pytest.raises(ExternalServiceException) as exc_info:
                await client._authorized_request("GET", "/test")

            assert "no está disponible" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_authorized_request_timeout_error(self, client):
        """Verifica manejo de timeout."""
        with patch("app.client.person_client.auth_service") as mock_auth:
            mock_auth.token = None
            mock_auth.login = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(ExternalServiceException) as exc_info:
                await client._authorized_request("GET", "/test")

            assert "no está disponible" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_authorized_request_validation_error_dict(self, client):
        """Verifica manejo de error de validación (dict response)."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Campo inválido"}

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "test_token"
            mock_request.return_value = mock_response

            with pytest.raises(ValidationException) as exc_info:
                await client._authorized_request("POST", "/test", json={})

            assert "Campo inválido" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_authorized_request_validation_error_list(self, client):
        """Verifica manejo de error de validación (list response)."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = [{"msg": "Error en campo"}]

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "test_token"
            mock_request.return_value = mock_response

            with pytest.raises(ValidationException) as exc_info:
                await client._authorized_request("POST", "/test", json={})

            assert "Error en campo" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_authorized_request_validation_error_generic(self, client):
        """Verifica manejo de error genérico de validación."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "error de validacion de datos"}

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "test_token"
            mock_request.return_value = mock_response

            with pytest.raises(ValidationException) as exc_info:
                await client._authorized_request("POST", "/test", json={})

            assert "institucional rechazó" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_authorized_request_json_parse_error(self, client):
        """Verifica manejo cuando json() falla."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("Invalid JSON")
        mock_response.text = "Internal Server Error"

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "test_token"
            mock_request.return_value = mock_response

            with pytest.raises(ValidationException) as exc_info:
                await client._authorized_request("GET", "/test")

            assert "Internal Server Error" in str(exc_info.value.message)


class TestPersonClientMethods:
    """Tests para los métodos públicos de PersonClient."""

    @pytest.fixture
    def client(self):
        """Cliente de test."""
        return PersonClient(base_url="http://test.local")

    @pytest.mark.asyncio
    async def test_create_person(self, client):
        """Verifica create_person."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"id": 1}
            result = await client.create_person({"name": "Test"})

            mock_request.assert_called_once_with(
                "POST", "/api/person/save", json={"name": "Test"}
            )
            assert result == {"id": 1}

    @pytest.mark.asyncio
    async def test_create_person_with_account(self, client):
        """Verifica create_person_with_account."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"id": 1, "account": True}
            result = await client.create_person_with_account({"name": "Test"})

            mock_request.assert_called_once_with(
                "POST", "/api/person/save-account", json={"name": "Test"}
            )
            assert result["account"] is True

    @pytest.mark.asyncio
    async def test_update_person(self, client):
        """Verifica update_person."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"updated": True}
            result = await client.update_person({"id": 1, "name": "Updated"})

            mock_request.assert_called_once_with(
                "POST", "/api/person/update", json={"id": 1, "name": "Updated"}
            )
            assert result == {"updated": True}

    @pytest.mark.asyncio
    async def test_update_person_account(self, client):
        """Verifica update_person_account."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"updated": True}
            await client.update_person_account({"id": 1})

            mock_request.assert_called_once_with(
                "POST", "/api/person/update-account", json={"id": 1}
            )

    @pytest.mark.asyncio
    async def test_get_by_id(self, client):
        """Verifica get_by_id."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"id": 123, "name": "Test"}
            result = await client.get_by_id(123)

            mock_request.assert_called_once_with("GET", "/api/person/search_id/123")
            assert result["id"] == 123

    @pytest.mark.asyncio
    async def test_get_by_identification(self, client):
        """Verifica get_by_identification."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"dni": "1234567890"}
            result = await client.get_by_identification("1234567890")

            mock_request.assert_called_once_with(
                "GET", "/api/person/search_identification/1234567890"
            )
            assert result["dni"] == "1234567890"

    @pytest.mark.asyncio
    async def test_get_by_external(self, client):
        """Verifica get_by_external."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"external": "ext-123"}
            await client.get_by_external("ext-123")

            mock_request.assert_called_once_with("GET", "/api/person/search/ext-123")

    @pytest.mark.asyncio
    async def test_change_state(self, client):
        """Verifica change_state."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"state": "inactive"}
            await client.change_state("ext-123")

            mock_request.assert_called_once_with(
                "GET", "/api/person/change_state/ext-123"
            )

    @pytest.mark.asyncio
    async def test_get_all_filter(self, client):
        """Verifica get_all_filter."""
        with patch.object(
            client, "_authorized_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = [{"id": 1}, {"id": 2}]
            result = await client.get_all_filter()

            mock_request.assert_called_once_with("GET", "/api/person/all_filter")
            assert len(result) == 2


class TestPersonClientErrorHandling:
    """Tests para manejo de errores específicos."""

    @pytest.fixture
    def client(self):
        """Cliente de test."""
        return PersonClient(base_url="http://test.local")

    @pytest.mark.asyncio
    async def test_error_response_with_detail(self, client):
        """Verifica manejo de error con 'detail'."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Detalle del error"}

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "test_token"
            mock_request.return_value = mock_response

            with pytest.raises(ValidationException) as exc_info:
                await client._authorized_request("GET", "/test")

            assert "Detalle del error" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_error_response_with_error_field(self, client):
        """Verifica manejo de error con campo 'error'."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Mensaje de error"}

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "test_token"
            mock_request.return_value = mock_response

            with pytest.raises(ValidationException) as exc_info:
                await client._authorized_request("GET", "/test")

            assert "Mensaje de error" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_error_response_list_with_string(self, client):
        """Verifica manejo de error como lista de strings."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = ["Error simple"]

        with (
            patch("app.client.person_client.auth_service") as mock_auth,
            patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock
            ) as mock_request,
        ):
            mock_auth.token = "test_token"
            mock_request.return_value = mock_response

            with pytest.raises(ValidationException) as exc_info:
                await client._authorized_request("GET", "/test")

            assert "Error simple" in str(exc_info.value.message)
