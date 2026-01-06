# tests/conftest.py
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.enums.rol import Role


@pytest.fixture
def mock_db_session():
    """Sesión simulada para evitar tocar la BD real en tests."""
    session = MagicMock()
    yield session


@pytest.fixture
def mock_admin_account():
    """Mock de una cuenta de administrador para autenticación."""
    account = MagicMock()
    account.id = 1
    account.email = "admin@test.com"
    account.role = Role.ADMINISTRATOR
    account.user_id = 1
    # Mock del usuario asociado (para endpoints que usan current_user.user.dni)
    account.user = MagicMock()
    account.user.dni = "1150696977"
    return account


@pytest.fixture
def mock_coach_account():
    """Mock de una cuenta de entrenador para autenticación."""
    account = MagicMock()
    account.id = 2
    account.email = "coach@test.com"
    account.role = Role.COACH
    account.user_id = 2
    return account


@pytest.fixture
def mock_intern_account():
    """Mock de una cuenta de pasante para autenticación."""
    account = MagicMock()
    account.id = 3
    account.email = "intern@test.com"
    account.role = Role.INTERN
    account.user_id = 3
    return account


@pytest.fixture
async def client(mock_db_session):
    """Cliente HTTP asíncrono sin autenticación (para tests públicos)."""
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


@pytest.fixture
async def admin_client(mock_db_session, mock_admin_account):
    """Cliente HTTP autenticado como administrador."""
    from app.core.database import get_db
    from app.utils.security import get_current_account, get_current_admin
    from main import app

    async def override_get_db():
        yield mock_db_session

    def override_get_current_account():
        return mock_admin_account

    def override_get_current_admin():
        return mock_admin_account

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_account] = override_get_current_account
    app.dependency_overrides[get_current_admin] = override_get_current_admin

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def coach_client(mock_db_session, mock_coach_account):
    """Cliente HTTP autenticado como entrenador."""
    from app.core.database import get_db
    from app.utils.security import get_current_account, get_current_coach
    from main import app

    async def override_get_db():
        yield mock_db_session

    def override_get_current_account():
        return mock_coach_account

    def override_get_current_coach():
        return mock_coach_account

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_account] = override_get_current_account
    app.dependency_overrides[get_current_coach] = override_get_current_coach

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def intern_client(mock_db_session, mock_intern_account):
    """Cliente HTTP autenticado como pasante."""
    from app.core.database import get_db
    from app.utils.security import get_current_account, get_current_staff
    from main import app

    async def override_get_db():
        yield mock_db_session

    def override_get_current_account():
        return mock_intern_account

    def override_get_current_staff():
        return mock_intern_account

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_account] = override_get_current_account
    app.dependency_overrides[get_current_staff] = override_get_current_staff

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
