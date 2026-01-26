"""
Pruebas de integración para el manejo global de errores.

Verifica:
- El servidor responde con mensajes amigables
- El servidor no se cae ante errores
- Las respuestas de error tienen estructura correcta
"""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def http_client():
    """Cliente HTTP asíncrono para pruebas."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


class TestErrorHandling:
    """Pruebas para verificar el manejo de errores."""

    @pytest.mark.asyncio
    async def test_server_survives_errors(self, http_client):
        """Verifica que el servidor sigue funcionando después de errores."""
        # Provocar error
        await http_client.get("/nonexistent-endpoint")

        # El servidor debe seguir funcionando
        response = await http_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_invalid_json_returns_error_not_crash(self, http_client):
        """Verifica que JSON inválido no hace crashear el servidor."""
        response = await http_client.post(
            "/api/v1/accounts/login",
            content="esto no es json válido",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code in [400, 422]

        # El servidor sigue vivo
        health = await http_client.get("/health/live")
        assert health.status_code == 200

    @pytest.mark.asyncio
    async def test_404_has_correct_structure(self, http_client):
        """Verifica que 404 tiene estructura correcta."""
        response = await http_client.get("/api/v1/recurso-inexistente")

        assert response.status_code == 404
        payload = response.json()
        assert "status" in payload or "detail" in payload

    @pytest.mark.asyncio
    async def test_validation_error_has_message(self, http_client):
        """Verifica que errores de validación tienen mensaje comprensible."""
        response = await http_client.post(
            "/api/v1/accounts/login",
            json={"email": "no-es-email"},  # Falta password
        )

        assert response.status_code == 422
        payload = response.json()
        assert "message" in payload or "detail" in payload


class TestErrorMessagesAreUserFriendly:
    """Verifica que los mensajes de error son amigables."""

    @pytest.mark.asyncio
    async def test_error_messages_not_expose_technical_details(self, http_client):
        """Verifica que los errores no exponen detalles técnicos."""
        response = await http_client.get("/health")

        if response.status_code != 200:
            payload = response.json()
            message = payload.get("message", "").lower()

            # No debe contener términos técnicos
            technical_terms = [
                "traceback",
                "exception",
                "stacktrace",
                "operationalerror",
                "connection refused",
            ]
            for term in technical_terms:
                assert term not in message, f"Mensaje expone término técnico: {term}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
