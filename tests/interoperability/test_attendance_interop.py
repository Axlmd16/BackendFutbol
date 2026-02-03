import pytest

from tests.interoperability.conftest import assert_response_schema


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_attendance_by_date_requires_auth(http_client):
    response = await http_client.get("/api/v1/attendances/by-date")

    assert response.status_code == 401
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_attendance_summary_requires_auth(http_client):
    response = await http_client.get("/api/v1/attendances/summary")

    assert response.status_code == 401
    payload = response.json()
    assert_response_schema(payload)
    assert payload["status"] == "error"
