"""Tests de integración para el router de Sprint Tests.

Cubre:
- POST /sprint-tests/: Crear Sprint Test
- GET /sprint-tests/: Listar Sprint Tests
- GET /sprint-tests/{test_id}: Obtener Sprint Test
- DELETE /sprint-tests/{test_id}: Eliminar Sprint Test
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def sprint_test_payload():
    """Data para crear un Sprint Test."""
    return {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "distance_meters": 30,
        "time_0_10_s": 1.85,
        "time_0_30_s": 3.95,
        "observations": "Good performance",
    }


# ==============================================
# POST /sprint-tests/ - Crear Sprint Test
# ==============================================


@pytest.mark.asyncio
async def test_create_sprint_test_success(admin_client, sprint_test_payload):
    """POST /sprint-tests/ debe crear un Sprint Test."""
    with patch(
        "app.services.routers.sprint_test_router.sprint_test_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 1
        mock_test.type = "sprint_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.distance_meters = 30
        mock_test.time_0_10_s = 1.85
        mock_test.time_0_30_s = 3.95
        mock_test.observations = "Good performance"
        mock_controller.add_test.return_value = mock_test

        response = await admin_client.post(
            "/api/v1/sprint-tests/",
            json=sprint_test_payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["distance_meters"] == 30


@pytest.mark.asyncio
async def test_create_sprint_test_athlete_not_found(admin_client):
    """POST /sprint-tests/ debe validar que el atleta exista."""
    from app.utils.exceptions import DatabaseException

    payload = {
        "athlete_id": 999,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "distance_meters": 30,
        "time_0_10_s": 1.85,
        "time_0_30_s": 3.95,
    }

    with patch(
        "app.services.routers.sprint_test_router.sprint_test_controller"
    ) as mock_controller:
        mock_controller.add_test.side_effect = DatabaseException("Atleta no existe")

        response = await admin_client.post(
            "/api/v1/sprint-tests/",
            json=payload,
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_sprint_test_validation_error(admin_client):
    """POST /sprint-tests/ debe retornar 422 con datos inválidos."""
    payload = {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "distance_meters": -10,  # Inválido: debe ser > 0
        "time_0_10_s": 1.85,
        "time_0_30_s": 3.95,
    }

    response = await admin_client.post(
        "/api/v1/sprint-tests/",
        json=payload,
    )

    assert response.status_code == 422


# ==============================================
# GET /sprint-tests/ - Listar Sprint Tests
# ==============================================


@pytest.mark.asyncio
async def test_list_sprint_tests_success(admin_client):
    """GET /sprint-tests/ debe listar Sprint Tests."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao

        mock_test = MagicMock()
        mock_test.id = 1
        mock_test.type = "sprint_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.distance_meters = 30
        mock_test.time_0_10_s = 1.85
        mock_test.time_0_30_s = 3.95
        mock_test.observations = None

        mock_dao.list_tests.return_value = [mock_test]

        response = await admin_client.get("/api/v1/sprint-tests/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1


@pytest.mark.asyncio
async def test_list_sprint_tests_empty(admin_client):
    """GET /sprint-tests/ debe retornar lista vacía."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao
        mock_dao.list_tests.return_value = []

        response = await admin_client.get("/api/v1/sprint-tests/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 0


# ==============================================
# GET /sprint-tests/{test_id} - Obtener Sprint Test
# ==============================================


@pytest.mark.asyncio
async def test_get_sprint_test_success(admin_client):
    """GET /sprint-tests/{test_id} debe obtener un Sprint Test."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao

        mock_test = MagicMock()
        mock_test.id = 1
        mock_test.type = "sprint_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.distance_meters = 30
        mock_test.time_0_10_s = 1.85
        mock_test.time_0_30_s = 3.95
        mock_test.observations = None

        mock_dao.get_test.return_value = mock_test

        response = await admin_client.get("/api/v1/sprint-tests/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == 1


@pytest.mark.asyncio
async def test_get_sprint_test_not_found(admin_client):
    """GET /sprint-tests/{test_id} debe retornar 404 si no existe."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao
        mock_dao.get_test.return_value = None

        response = await admin_client.get("/api/v1/sprint-tests/999")

        assert response.status_code == 404


# ==============================================
# DELETE /sprint-tests/{test_id} - Eliminar Sprint Test
# ==============================================


@pytest.mark.asyncio
async def test_delete_sprint_test_success(admin_client):
    """DELETE /sprint-tests/{test_id} debe eliminar un Sprint Test."""
    with patch(
        "app.services.routers.sprint_test_router.test_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = True

        response = await admin_client.delete("/api/v1/sprint-tests/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


@pytest.mark.asyncio
async def test_delete_sprint_test_not_found(admin_client):
    """DELETE /sprint-tests/{test_id} debe retornar 404 si no existe."""
    with patch(
        "app.services.routers.sprint_test_router.test_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = False

        response = await admin_client.delete("/api/v1/sprint-tests/999")

        assert response.status_code == 404
