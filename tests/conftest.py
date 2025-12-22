# tests/conftest.py
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_db_session():
    """Sesión simulada para evitar tocar la BD real en tests."""
    session = MagicMock()
    yield session


@pytest.fixture
async def client(mock_db_session):
    """Cliente HTTP asíncrono con override de dependencia get_db."""
    from app.core.database import get_db
    from main import app

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Limpiar overrides después de cada test
    app.dependency_overrides.clear()
