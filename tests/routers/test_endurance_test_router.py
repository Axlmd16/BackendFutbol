"""Tests de integración para el router de Endurance Tests.

Cubre:
- POST /endurance-tests/: Crear Endurance Test
- GET /endurance-tests/: Listar Endurance Tests
- GET /endurance-tests/{test_id}: Obtener Endurance Test
- DELETE /endurance-tests/{test_id}: Eliminar Endurance Test
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def endurance_test_payload():
    """Data para crear un Endurance Test."""
    return {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "min_duration": 36,
        "total_distance_m": 6000,
        "observations": "Completed test",
    }


# ==============================================
# POST /endurance-tests/ - Crear Endurance Test
# ==============================================


@pytest.mark.asyncio
async def test_create_endurance_test_success(admin_client, endurance_test_payload):
    """POST /endurance-tests/ debe crear un Endurance Test."""
    with patch(
        "app.services.routers.endurance_test_router.endurance_test_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 3
        mock_test.type = "endurance_test"
        mock_test.test_type = "endurance_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.min_duration = 36
        mock_test.total_distance_m = 6000
        mock_test.observations = "Completed test"
        mock_test.created_at = datetime.now()
        mock_test.updated_at = None
        mock_test.is_active = True
        mock_controller.add_test.return_value = mock_test

        response = await admin_client.post(
            "/api/v1/endurance-tests/",
            json=endurance_test_payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["min_duration"] == 36


@pytest.mark.asyncio
async def test_create_endurance_test_athlete_not_found(admin_client):
    """POST /endurance-tests/ debe validar que el atleta exista."""
    from app.utils.exceptions import DatabaseException

    payload = {
        "athlete_id": 999,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "min_duration": 36,
        "total_distance_m": 6000,
    }

    with patch(
        "app.services.routers.endurance_test_router.endurance_test_controller"
    ) as mock_controller:
        mock_controller.add_test.side_effect = DatabaseException("Atleta no existe")

        response = await admin_client.post(
            "/api/v1/endurance-tests/",
            json=payload,
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_endurance_test_validation_error(admin_client):
    """POST /endurance-tests/ debe retornar 422 con datos inválidos."""
    payload = {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "min_duration": -10,  # Inválido: debe ser > 0
        "total_distance_m": 6000,
    }

    response = await admin_client.post(
        "/api/v1/endurance-tests/",
        json=payload,
    )

    assert response.status_code == 422


# ==============================================
# GET /endurance-tests/ - Listar Endurance Tests
# ==============================================


@pytest.mark.asyncio
async def test_list_endurance_tests_success(admin_client, mock_db_session):
    """GET /endurance-tests/ debe listar Endurance Tests."""
    mock_test = MagicMock()
    mock_test.id = 3
    mock_test.type = "endurance_test"
    mock_test.test_type = "endurance_test"
    mock_test.date = datetime.now()
    mock_test.athlete_id = 5
    mock_test.evaluation_id = 1
    mock_test.min_duration = 36
    mock_test.total_distance_m = 6000
    mock_test.observations = None
    mock_test.created_at = datetime.now()
    mock_test.updated_at = None
    mock_test.is_active = True

    query_mock = mock_db_session.query.return_value
    filter_mock = query_mock.filter.return_value
    offset_mock = filter_mock.offset.return_value
    limit_mock = offset_mock.limit.return_value
    limit_mock.all.return_value = [mock_test]

    response = await admin_client.get("/api/v1/endurance-tests/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 1


@pytest.mark.asyncio
async def test_list_endurance_tests_empty(admin_client, mock_db_session):
    """GET /endurance-tests/ debe retornar lista vacía."""
    query_mock = mock_db_session.query.return_value
    filter_mock = query_mock.filter.return_value
    offset_mock = filter_mock.offset.return_value
    limit_mock = offset_mock.limit.return_value
    limit_mock.all.return_value = []

    response = await admin_client.get("/api/v1/endurance-tests/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 0


# ==============================================
# GET /endurance-tests/{test_id} - Obtener Endurance Test
# ==============================================


@pytest.mark.asyncio
async def test_get_endurance_test_success(admin_client):
    """GET /endurance-tests/{test_id} debe obtener un Endurance Test."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao

        mock_test = MagicMock()
        mock_test.id = 3
        mock_test.type = "endurance_test"
        mock_test.test_type = "endurance_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.min_duration = 36
        mock_test.total_distance_m = 6000
        mock_test.observations = None
        mock_test.created_at = datetime.now()
        mock_test.updated_at = None
        mock_test.is_active = True

        mock_dao.get_test.return_value = mock_test

        response = await admin_client.get("/api/v1/endurance-tests/3")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == 3


@pytest.mark.asyncio
async def test_get_endurance_test_not_found(admin_client):
    """GET /endurance-tests/{test_id} debe retornar 404 si no existe."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao
        mock_dao.get_test.return_value = None

        response = await admin_client.get("/api/v1/endurance-tests/999")

        assert response.status_code == 404


# ==============================================
# DELETE /endurance-tests/{test_id} - Eliminar Endurance Test
# ==============================================


@pytest.mark.asyncio
async def test_delete_endurance_test_success(admin_client):
    """DELETE /endurance-tests/{test_id} debe eliminar un Endurance Test."""
    with patch(
        "app.services.routers.endurance_test_router.test_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = True

        response = await admin_client.delete("/api/v1/endurance-tests/3")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


@pytest.mark.asyncio
async def test_delete_endurance_test_not_found(admin_client):
    """DELETE /endurance-tests/{test_id} debe retornar 404 si no existe."""
    with patch(
        "app.services.routers.endurance_test_router.test_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = False

        response = await admin_client.delete("/api/v1/endurance-tests/999")

        assert response.status_code == 404
