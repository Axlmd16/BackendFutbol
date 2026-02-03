import pytest

from tests.interoperability.conftest import assert_response_schema


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_users_me_requires_auth(http_client):
    response = await http_client.get("/api/v1/users/me")

    assert response.status_code == 401
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_users_list_requires_auth(http_client):
    response = await http_client.get("/api/v1/users/all")

    assert response.status_code == 401
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"
