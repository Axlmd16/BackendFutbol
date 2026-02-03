import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def http_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def assert_response_schema(payload: dict, expect_errors: bool = False) -> None:
    assert "status" in payload
    assert "message" in payload
    assert "data" in payload
    if expect_errors:
        assert "errors" in payload
