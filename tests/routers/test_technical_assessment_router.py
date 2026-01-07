"""Tests de integración para el router de Technical Assessments.

Cubre:
- POST /technical-assessments/: Crear Technical Assessment
- GET /technical-assessments/: Listar Technical Assessments
- GET /technical-assessments/{test_id}: Obtener Technical Assessment
- DELETE /technical-assessments/{test_id}: Eliminar Technical Assessment
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def technical_assessment_payload():
    """Data para crear un Technical Assessment."""
    return {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "ball_control": "Excellent",
        "short_pass": "Excellent",
        "long_pass": "Good",
        "shooting": "Good",
        "dribbling": "Excellent",
        "observations": "Good technique",
    }


# ==============================================
# POST /technical-assessments/ - Crear Technical Assessment
# ==============================================


@pytest.mark.asyncio
async def test_create_technical_assessment_success(
    admin_client, technical_assessment_payload
):
    """POST /technical-assessments/ debe crear un Technical Assessment."""
    with patch(
        "app.services.routers.technical_assessment_router.technical_assessment_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 4
        mock_test.type = "technical_assessment"
        mock_test.test_type = "technical_assessment"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.ball_control = "Excellent"
        mock_test.short_pass = "Excellent"
        mock_test.long_pass = "Good"
        mock_test.shooting = "Good"
        mock_test.dribbling = "Excellent"
        mock_test.observations = "Good technique"
        mock_test.created_at = datetime.now()
        mock_test.updated_at = None
        mock_test.is_active = True
        mock_controller.add_test.return_value = mock_test

        response = await admin_client.post(
            "/api/v1/technical-assessments/",
            json=technical_assessment_payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["ball_control"] == "Excellent"
        mock_controller.add_test.assert_called_once()
        called_payload = mock_controller.add_test.call_args.kwargs["payload"]
        assert (
            called_payload.ball_control.value
            == technical_assessment_payload["ball_control"]
        )


@pytest.mark.asyncio
async def test_create_technical_assessment_athlete_not_found(admin_client):
    """POST /technical-assessments/ debe validar que el atleta exista."""
    from app.utils.exceptions import DatabaseException

    payload = {
        "athlete_id": 999,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "ball_control": "Excellent",
        "short_pass": "Excellent",
        "long_pass": "Good",
        "shooting": "Good",
        "dribbling": "Excellent",
    }

    with patch(
        "app.services.routers.technical_assessment_router.technical_assessment_controller"
    ) as mock_controller:
        mock_controller.add_test.side_effect = DatabaseException("Atleta no existe")

        response = await admin_client.post(
            "/api/v1/technical-assessments/",
            json=payload,
        )

        assert response.status_code == 400


# ==============================================
# GET /technical-assessments/ - Listar Technical Assessments
# ==============================================


@pytest.mark.asyncio
async def test_list_technical_assessments_success(admin_client, mock_db_session):
    """GET /technical-assessments/ debe listar Technical Assessments."""
    with patch(
        "app.services.routers.technical_assessment_router.technical_assessment_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 4
        mock_test.type = "technical_assessment"
        mock_test.test_type = "technical_assessment"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.ball_control = "Excellent"
        mock_test.short_pass = "Excellent"
        mock_test.long_pass = "Good"
        mock_test.shooting = "Good"
        mock_test.dribbling = "Excellent"
        mock_test.observations = None
        mock_test.created_at = datetime.now()
        mock_test.updated_at = None
        mock_test.is_active = True

        mock_controller.list_tests.return_value = ([mock_test], 1)

        response = await admin_client.get("/api/v1/technical-assessments/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_list_technical_assessments_empty(admin_client, mock_db_session):
    """GET /technical-assessments/ debe retornar lista vacía."""
    with patch(
        "app.services.routers.technical_assessment_router.technical_assessment_controller"
    ) as mock_controller:
        mock_controller.list_tests.return_value = ([], 0)

        response = await admin_client.get("/api/v1/technical-assessments/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total"] == 0
        assert len(data["data"]["items"]) == 0


# ==============================================
# GET /technical-assessments/{test_id} - Obtener Technical Assessment
# ==============================================


@pytest.mark.asyncio
async def test_get_technical_assessment_success(admin_client):
    """GET /technical-assessments/{test_id} debe obtener un Technical Assessment."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao

        mock_test = MagicMock()
        mock_test.id = 4
        mock_test.type = "technical_assessment"
        mock_test.test_type = "technical_assessment"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.ball_control = "Excellent"
        mock_test.short_pass = "Excellent"
        mock_test.long_pass = "Good"
        mock_test.shooting = "Good"
        mock_test.dribbling = "Excellent"
        mock_test.observations = None
        mock_test.created_at = datetime.now()
        mock_test.updated_at = None
        mock_test.is_active = True

        mock_dao.get_test.return_value = mock_test

        response = await admin_client.get("/api/v1/technical-assessments/4")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == 4


@pytest.mark.asyncio
async def test_get_technical_assessment_not_found(admin_client):
    """GET /technical-assessments/{test_id} debe retornar 404 si no existe."""
    with patch("app.dao.test_dao.TestDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao_class.return_value = mock_dao
        mock_dao.get_test.return_value = None

        response = await admin_client.get("/api/v1/technical-assessments/999")

        assert response.status_code == 404


# ==============================================
# DELETE /technical-assessments/{test_id} - Eliminar Technical Assessment
# ==============================================


@pytest.mark.asyncio
async def test_delete_technical_assessment_success(admin_client):
    """DELETE /technical-assessments/{test_id} debe eliminar un Technical Assessment."""
    with patch(
        "app.services.routers.technical_assessment_router.technical_assessment_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = True

        response = await admin_client.delete("/api/v1/technical-assessments/4")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


@pytest.mark.asyncio
async def test_delete_technical_assessment_not_found(admin_client):
    """DELETE /technical-assessments/{test_id} debe retornar 404 si no existe."""
    with patch(
        "app.services.routers.technical_assessment_router.technical_assessment_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = False

        response = await admin_client.delete("/api/v1/technical-assessments/999")

        assert response.status_code == 404
