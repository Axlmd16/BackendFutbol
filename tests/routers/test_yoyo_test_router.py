"""Tests de integración para el router de Yoyo Tests.

Cubre:
- POST /yoyo-tests/: Crear Yoyo Test
- GET /yoyo-tests/: Listar Yoyo Tests
- GET /yoyo-tests/{test_id}: Obtener Yoyo Test
- DELETE /yoyo-tests/{test_id}: Eliminar Yoyo Test
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def yoyo_test_payload():
    """Data para crear un Yoyo Test."""
    return {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "shuttle_count": 47,
        "final_level": "18.2",
        "failures": 2,
        "observations": "Good effort",
    }


# ==============================================
# POST /yoyo-tests/ - Crear Yoyo Test
# ==============================================


@pytest.mark.asyncio
async def test_create_yoyo_test_success(admin_client, yoyo_test_payload):
    """POST /yoyo-tests/ debe crear un Yoyo Test."""
    with patch(
        "app.services.routers.yoyo_test_router.yoyo_test_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 2
        mock_test.type = "yoyo_test"
        mock_test.test_type = "yoyo_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.shuttle_count = 47
        mock_test.final_level = "18.2"
        mock_test.failures = 2
        mock_test.observations = "Good effort"
        mock_test.created_at = datetime.now()
        mock_test.updated_at = None
        mock_test.is_active = True
        mock_controller.add_test.return_value = mock_test

        response = await admin_client.post(
            "/api/v1/yoyo-tests/",
            json=yoyo_test_payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["shuttle_count"] == 47


@pytest.mark.asyncio
async def test_create_yoyo_test_athlete_not_found(admin_client):
    """POST /yoyo-tests/ debe validar que el atleta exista."""
    from app.utils.exceptions import DatabaseException

    payload = {
        "athlete_id": 999,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "shuttle_count": 47,
        "final_level": "18.2",
        "failures": 2,
    }

    with patch(
        "app.services.routers.yoyo_test_router.yoyo_test_controller"
    ) as mock_controller:
        mock_controller.add_test.side_effect = DatabaseException("Atleta no existe")

        response = await admin_client.post(
            "/api/v1/yoyo-tests/",
            json=payload,
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_yoyo_test_validation_error(admin_client):
    """POST /yoyo-tests/ debe retornar 422 con datos inválidos."""
    payload = {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "shuttle_count": -5,  # Inválido: debe ser > 0
        "final_level": "18.2",
        "failures": 2,
    }

    response = await admin_client.post(
        "/api/v1/yoyo-tests/",
        json=payload,
    )

    assert response.status_code == 422


# ==============================================
# GET /yoyo-tests/ - Listar Yoyo Tests
# ==============================================


@pytest.mark.asyncio
async def test_list_yoyo_tests_success(admin_client, mock_db_session):
    """GET /yoyo-tests/ debe listar Yoyo Tests."""
    mock_test = MagicMock()
    mock_test.id = 2
    mock_test.type = "yoyo_test"
    mock_test.test_type = "yoyo_test"
    mock_test.date = datetime.now()
    mock_test.athlete_id = 5
    mock_test.evaluation_id = 1
    mock_test.shuttle_count = 47
    mock_test.final_level = "18.2"
    mock_test.failures = 2
    mock_test.observations = None
    mock_test.created_at = datetime.now()
    mock_test.updated_at = None
    mock_test.is_active = True

    query_mock = mock_db_session.query.return_value
    filter_mock = query_mock.filter.return_value
    offset_mock = filter_mock.offset.return_value
    limit_mock = offset_mock.limit.return_value
    limit_mock.all.return_value = [mock_test]

    response = await admin_client.get("/api/v1/yoyo-tests/")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 1


@pytest.mark.asyncio
async def test_list_yoyo_tests_empty(admin_client, mock_db_session):
    """GET /yoyo-tests/ debe retornar lista vacía."""
    query_mock = mock_db_session.query.return_value
    filter_mock = query_mock.filter.return_value
    offset_mock = filter_mock.offset.return_value
    limit_mock = offset_mock.limit.return_value
    limit_mock.all.return_value = []

    response = await admin_client.get("/api/v1/yoyo-tests/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 0


# ==============================================
# GET /yoyo-tests/{test_id} - Obtener Yoyo Test
# ==============================================


@pytest.mark.asyncio
async def test_get_yoyo_test_success(admin_client):
    """GET /yoyo-tests/{test_id} debe obtener un Yoyo Test."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao

        mock_test = MagicMock()
        mock_test.id = 2
        mock_test.type = "yoyo_test"
        mock_test.test_type = "yoyo_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.shuttle_count = 47
        mock_test.final_level = "18.2"
        mock_test.failures = 2
        mock_test.observations = None
        mock_test.created_at = datetime.now()
        mock_test.updated_at = None
        mock_test.is_active = True

        mock_dao.get_test.return_value = mock_test

        response = await admin_client.get("/api/v1/yoyo-tests/2")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == 2


@pytest.mark.asyncio
async def test_get_yoyo_test_not_found(admin_client):
    """GET /yoyo-tests/{test_id} debe retornar 404 si no existe."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao
        mock_dao.get_test.return_value = None

        response = await admin_client.get("/api/v1/yoyo-tests/999")

        assert response.status_code == 404


# ==============================================
# DELETE /yoyo-tests/{test_id} - Eliminar Yoyo Test
# ==============================================


@pytest.mark.asyncio
async def test_delete_yoyo_test_success(admin_client):
    """DELETE /yoyo-tests/{test_id} debe eliminar un Yoyo Test."""
    with patch(
        "app.services.routers.yoyo_test_router.test_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = True

        response = await admin_client.delete("/api/v1/yoyo-tests/2")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


@pytest.mark.asyncio
async def test_delete_yoyo_test_not_found(admin_client):
    """DELETE /yoyo-tests/{test_id} debe retornar 404 si no existe."""
    with patch(
        "app.services.routers.yoyo_test_router.test_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = False

        response = await admin_client.delete("/api/v1/yoyo-tests/999")

        assert response.status_code == 404
