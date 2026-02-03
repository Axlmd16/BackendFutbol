"""Tests de integración para los endpoints del router de evaluaciones.

Cubre únicamente los endpoints propios del recurso Evaluations:
- POST /evaluations/: Crear evaluación
- GET /evaluations/: Listar evaluaciones
- GET /evaluations/user/{user_id}: Listar evaluaciones de usuario
- GET /evaluations/{evaluation_id}: Obtener evaluación
- PUT /evaluations/{evaluation_id}: Actualizar evaluación
- DELETE /evaluations/{evaluation_id}: Eliminar evaluación
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# ==============================================
# FIXTURES
# ==============================================


@pytest.fixture
def mock_evaluation_data():
    """Data para crear una evaluación."""
    return {
        "name": "Evaluación Física",
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:30",
        "user_id": 1,
        "location": "Cancha Principal",
        "observations": "Test initial",
    }


# ==============================================
# TESTS: POST /evaluations/
# ==============================================


@pytest.mark.asyncio
async def test_create_evaluation_success(admin_client, mock_evaluation_data):
    """POST /evaluations/ debe crear una evaluación exitosamente."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        # Crear un mock que represente la evaluación retornada por el DAO
        mock_evaluation = MagicMock()
        mock_evaluation.id = 1
        mock_evaluation.name = "Evaluación Física"
        mock_evaluation.date = datetime.fromisoformat(mock_evaluation_data["date"])
        mock_evaluation.time = "10:30"
        mock_evaluation.user_id = 1
        mock_evaluation.location = "Cancha Principal"
        mock_evaluation.observations = "Test initial"
        mock_evaluation.created_at = datetime.now()
        mock_evaluation.updated_at = None
        mock_evaluation.is_active = True

        mock_controller.create_evaluation.return_value = mock_evaluation

        response = await admin_client.post(
            "/api/v1/evaluations/",
            json=mock_evaluation_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Evaluación creada correctamente"
        mock_controller.create_evaluation.assert_called_once()
        called_payload = mock_controller.create_evaluation.call_args.kwargs["payload"]
        assert called_payload.name == mock_evaluation_data["name"]


@pytest.mark.asyncio
async def test_create_evaluation_validation_error(admin_client):
    """POST /evaluations/ debe validar datos requeridos."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        from app.utils.exceptions import DatabaseException

        mock_controller.create_evaluation.side_effect = DatabaseException(
            "La fecha de evaluación no puede ser anterior a hoy"
        )

        response = await admin_client.post(
            "/api/v1/evaluations/",
            json={
                "name": "Evaluación Pasada",
                "date": (datetime.now() - timedelta(days=1)).isoformat(),
                "time": "10:30",
                "user_id": 1,
            },
        )

        assert response.status_code == 400


# ==============================================
# TESTS: GET /evaluations/
# ==============================================


@pytest.mark.asyncio
async def test_list_evaluations_success(admin_client):
    """GET /evaluations/ debe listar evaluaciones."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_eval = MagicMock()
        mock_eval.id = 1
        mock_eval.name = "Evaluación Física"
        mock_eval.date = datetime.now()
        mock_eval.time = "10:30"
        mock_eval.location = "Cancha Principal"
        mock_eval.user_id = 1
        mock_eval.observations = "Test initial"
        mock_eval.created_at = datetime.now()
        mock_eval.updated_at = None
        mock_eval.is_active = True
        mock_controller.list_evaluations_paginated.return_value = ([mock_eval], 1)

        response = await admin_client.get("/api/v1/evaluations/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1
        assert data["data"]["page"] == 1
        assert data["data"]["limit"] == 10  # Valor por defecto


@pytest.mark.asyncio
async def test_list_evaluations_with_pagination(admin_client):
    """GET /evaluations/?page=1&limit=10 debe paginar."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_controller.list_evaluations_paginated.return_value = ([], 0)

        response = await admin_client.get("/api/v1/evaluations/?page=1&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []
        mock_controller.list_evaluations_paginated.assert_called_once()


# ==============================================
# TESTS: GET /evaluations/{evaluation_id}
# ==============================================


@pytest.mark.asyncio
async def test_get_evaluation_success(admin_client):
    """GET /evaluations/{id} debe obtener una evaluación."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_eval = MagicMock()
        mock_eval.id = 1
        mock_eval.name = "Evaluación Física"
        mock_eval.date = datetime.now()
        mock_eval.time = "10:30"
        mock_eval.location = "Cancha Principal"
        mock_eval.user_id = 1
        mock_eval.observations = "Test initial"
        mock_eval.tests = []
        mock_eval.created_at = datetime.now()
        mock_eval.updated_at = None
        mock_eval.is_active = True
        mock_controller.get_evaluation.return_value = mock_eval

        response = await admin_client.get("/api/v1/evaluations/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == 1


@pytest.mark.asyncio
async def test_get_evaluation_not_found(admin_client):
    """GET /evaluations/{id} debe retornar 404 si no existe."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_controller.get_evaluation.return_value = None

        response = await admin_client.get("/api/v1/evaluations/999")

        assert response.status_code == 404


# ==============================================
# TESTS: PUT /evaluations/{evaluation_id}
# ==============================================


@pytest.mark.asyncio
async def test_update_evaluation_success(admin_client):
    """PUT /evaluations/{id} debe actualizar una evaluación."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_eval = MagicMock()
        mock_eval.id = 1
        mock_eval.name = "Evaluación Actualizada"
        mock_eval.date = datetime.now()
        mock_eval.time = "11:00"
        mock_eval.location = "Cancha Auxiliar"
        mock_eval.user_id = 1
        mock_eval.observations = "Updated"
        mock_eval.created_at = datetime.now()
        mock_eval.updated_at = None
        mock_eval.is_active = True
        mock_controller.update_evaluation.return_value = mock_eval

        response = await admin_client.put(
            "/api/v1/evaluations/1",
            json={
                "name": "Evaluación Actualizada",
                "time": "11:00",
                "location": "Cancha Auxiliar",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "Evaluación Actualizada"
        mock_controller.update_evaluation.assert_called_once()
        called_payload = mock_controller.update_evaluation.call_args.kwargs["payload"]
        assert called_payload.name == "Evaluación Actualizada"


@pytest.mark.asyncio
async def test_update_evaluation_not_found(admin_client):
    """PUT /evaluations/{id} debe retornar 404 si no existe."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_controller.update_evaluation.return_value = None

        response = await admin_client.put(
            "/api/v1/evaluations/999",
            json={"name": "Nueva Evaluación"},
        )

        assert response.status_code == 404


# ==============================================
# TESTS: DELETE /evaluations/{evaluation_id}
# ==============================================


@pytest.mark.asyncio
async def test_delete_evaluation_success(admin_client):
    """DELETE /evaluations/{id} debe eliminar una evaluación."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_controller.delete_evaluation.return_value = True

        response = await admin_client.delete("/api/v1/evaluations/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Evaluación eliminada correctamente"


@pytest.mark.asyncio
async def test_delete_evaluation_not_found(admin_client):
    """DELETE /evaluations/{id} debe retornar 404 si no existe."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_controller.delete_evaluation.return_value = False

        response = await admin_client.delete("/api/v1/evaluations/999")

        assert response.status_code == 404


# ==============================================
# TESTS: GET /evaluations/user/{user_id}
# ==============================================


@pytest.mark.asyncio
async def test_list_user_evaluations_success(admin_client):
    """GET /evaluations/user/{user_id} debe listar evaluaciones de usuario."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_eval = MagicMock()
        mock_eval.id = 1
        mock_eval.name = "Evaluación Física"
        mock_eval.date = datetime.now()
        mock_eval.time = "10:30"
        mock_eval.user_id = 1
        mock_eval.location = None
        mock_eval.observations = None
        mock_eval.created_at = datetime.now()
        mock_eval.updated_at = None
        mock_eval.is_active = True
        mock_controller.list_evaluations_by_user.return_value = [mock_eval]

        response = await admin_client.get("/api/v1/evaluations/user/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1
