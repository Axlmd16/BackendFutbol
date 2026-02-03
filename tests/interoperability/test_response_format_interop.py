import pytest

from tests.interoperability.conftest import assert_response_schema


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_health_response_schema(http_client):
    response = await http_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "success"


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_not_found_returns_standard_schema(http_client):
    response = await http_client.get("/api/v1/endpoint-que-no-existe")

    assert response.status_code == 404
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"
