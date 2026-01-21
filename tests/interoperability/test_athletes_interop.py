import pytest

from tests.interoperability.conftest import assert_response_schema


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_register_unl_validation_error_schema(http_client):
    response = await http_client.post("/api/v1/athletes/register-unl", json={})

    assert response.status_code == 422
    payload = response.json()
    assert_response_schema(payload, expect_errors=True)
    assert payload["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_register_minor_validation_error_schema(http_client):
    response = await http_client.post("/api/v1/athletes/register-minor", json={})

    assert response.status_code == 422
    payload = response.json()
    assert_response_schema(payload, expect_errors=True)
    assert payload["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_athletes_list_requires_auth(http_client):
    response = await http_client.get("/api/v1/athletes/all")

    assert response.status_code == 401
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"
