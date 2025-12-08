# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def mock_db_session():
    """Sesion simulada para evitar tocar la BD real en tests."""

    # MagicMock con la interfaz básica de Session
    session = MagicMock()
    yield session


@pytest.fixture
async def client(mock_db_session):
    """Cliente HTTP asíncrono con override de dependencia get_db."""

    from app.core.database import get_db

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app, lifespan="off")

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_db, None)
