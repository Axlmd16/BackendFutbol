# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport

from app.utils.security import CurrentUser


@pytest.fixture
def mock_db_session():
    """Sesión simulada para evitar tocar la BD real en tests."""
    session = MagicMock()
    yield session


@pytest.fixture
async def client(mock_db_session):
    """Cliente HTTP asíncrono con override de dependencia get_db."""
    from main import app
    from app.core.database import get_db

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Limpiar overrides después de cada test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_current_user():
    """
    Mock de usuario autenticado para inyectar en dependencias.
    
    Simula un usuario con rol ADMIN que pasó autenticación JWT.
    """
    return CurrentUser(
        id=1,
        email="test@test.com",
        role="ADMIN",
        external_id="ext-test-123",
        is_active=True
    )


@pytest.fixture
def override_authentication(mock_current_user):
    """
    Fixture para sobreescribir la autenticación en pruebas.
    
    Uso:
        def test_protected_endpoint(client, override_authentication):
            # El endpoint estará autenticado automáticamente
            response = await client.get("/protected-route")
    """
    from main import app
    # Nota: get_current_user debe ser implementado en un módulo de autenticación
    # Por ahora, este es un placeholder para futuras implementaciones
    
    # async def _override_auth():
    #     return mock_current_user
    
    # app.dependency_overrides[get_current_user] = _override_auth
    
    yield
    
    # Cleanup
    # if get_current_user in app.dependency_overrides:
    #     del app.dependency_overrides[get_current_user]