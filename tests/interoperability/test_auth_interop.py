import pytest

from tests.interoperability.conftest import assert_response_schema


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_login_invalid_credentials_returns_schema(http_client):
    response = await http_client.post(
        "/api/v1/accounts/login",
        json={"email": "noexiste@test.com", "password": "WrongPass123!"},
    )

    assert response.status_code == 401
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_refresh_invalid_token_returns_schema(http_client):
    response = await http_client.post(
        "/api/v1/accounts/refresh",
        json={"refresh_token": "invalid.token.value"},
    )

    assert response.status_code in (400, 401)
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_change_password_requires_auth(http_client):
    response = await http_client.post(
        "/api/v1/accounts/change-password",
        json={
            "current_password": "Current123!",
            "new_password": "NewPass123!",
            "confirm_password": "NewPass123!",
        },
    )

    assert response.status_code == 401
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"
