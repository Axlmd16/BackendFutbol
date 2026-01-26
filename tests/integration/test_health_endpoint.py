"""
Pruebas de integración para los endpoints de health check.

Verifica:
- Health check general
- Liveness y Readiness (para Kubernetes/Docker)
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from main import app


@pytest.fixture
async def http_client():
    """Cliente HTTP asíncrono para pruebas."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


class TestHealthEndpoints:
    """Pruebas para los endpoints de health check."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, http_client):
        """Verifica que /health retorna información completa."""
        response = await http_client.get("/health")

        assert response.status_code == 200
        payload = response.json()

        assert payload["status"] == "success"
        assert payload["data"]["app_name"] == settings.APP_NAME
        assert "database" in payload["data"]
        assert payload["data"]["database"] in ["connected", "disconnected"]

    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, http_client):
        """Verifica que /health/live indica que la app está viva."""
        response = await http_client.get("/health/live")

        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, http_client):
        """Verifica que /health/ready indica si puede recibir tráfico."""
        response = await http_client.get("/health/ready")

        assert response.status_code in [200, 503]
        payload = response.json()

        if response.status_code == 200:
            assert payload["status"] == "ready"
        else:
            assert payload["status"] == "not_ready"

    @pytest.mark.asyncio
    async def test_info_endpoint(self, http_client):
        """Verifica que /info retorna información de la API."""
        response = await http_client.get("/info")

        assert response.status_code == 200
        payload = response.json()
        assert "name" in payload["data"]
        assert "version" in payload["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
