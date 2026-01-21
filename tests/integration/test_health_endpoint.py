import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from main import app


@pytest.fixture
async def http_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_health_endpoint_returns_expected_payload(http_client):
    response = await http_client.get("/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "success"
    assert payload["data"]["app_name"] == settings.APP_NAME
    assert payload["data"]["version"] == settings.APP_VERSION
