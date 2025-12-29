"""Tests de integración para los endpoints del router de evaluaciones.

Cubre:
- POST /evaluations/: Crear evaluación
- GET /evaluations/: Listar evaluaciones
- GET /evaluations/user/{user_id}: Listar evaluaciones de usuario
- GET /evaluations/{evaluation_id}: Obtener evaluación
- PUT /evaluations/{evaluation_id}: Actualizar evaluación
- DELETE /evaluations/{evaluation_id}: Eliminar evaluación
- POST /evaluations/{evaluation_id}/sprint-tests: Agregar Sprint Test
- POST /evaluations/{evaluation_id}/yoyo-tests: Agregar Yoyo Test
- POST /evaluations/{evaluation_id}/endurance-tests: Agregar Endurance Test
- POST /evaluations/{evaluation_id}/technical-assessments: Agregar Technical Assessment
- GET /evaluations/{evaluation_id}/tests: Listar tests
- DELETE /evaluations/tests/{test_id}: Eliminar test
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


@pytest.fixture
def mock_sprint_test_data():
    """Data para agregar un Sprint Test."""
    return {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "distance_meters": 30,
        "time_0_10_s": 1.85,
        "time_0_30_s": 3.95,
        "observations": "Good performance",
    }


@pytest.fixture
def mock_yoyo_test_data():
    """Data para agregar un Yoyo Test."""
    return {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "shuttle_count": 47,
        "final_level": "18.2",
        "failures": 2,
        "observations": "Excellent aerobic capacity",
    }


@pytest.fixture
def mock_endurance_test_data():
    """Data para agregar un Endurance Test."""
    return {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "min_duration": 12,
        "total_distance_m": 2500,
        "observations": "Cooper test",
    }


@pytest.fixture
def mock_technical_assessment_data():
    """Data para agregar una Technical Assessment."""
    return {
        "athlete_id": 5,
        "date": datetime.now().isoformat(),
        "evaluation_id": 1,
        "ball_control": "MUY_ALTO",
        "short_pass": "ALTO",
        "long_pass": "MEDIO",
        "shooting": "ALTO",
        "dribbling": "MUY_ALTO",
        "observations": "Excellent technical skills",
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
        mock_controller.list_evaluations.return_value = [mock_eval]

        response = await admin_client.get("/api/v1/evaluations/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1


@pytest.mark.asyncio
async def test_list_evaluations_with_pagination(admin_client):
    """GET /evaluations/?skip=0&limit=10 debe paginar."""
    with patch(
        "app.services.routers.evaluation_router.evaluation_controller"
    ) as mock_controller:
        mock_controller.list_evaluations.return_value = []

        response = await admin_client.get("/api/v1/evaluations/?skip=0&limit=10")

        assert response.status_code == 200
        mock_controller.list_evaluations.assert_called_once()


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
# TESTS: POST /evaluations/{id}/sprint-tests
# ==============================================


@pytest.mark.asyncio
async def test_add_sprint_test_success(admin_client, mock_sprint_test_data):
    """POST /evaluations/{id}/sprint-tests debe agregar un Sprint Test."""
    with patch(
        "app.services.routers.evaluation_router.sprint_test_controller"
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
        mock_test.observations = None
        mock_controller.add_test.return_value = mock_test

        response = await admin_client.post(
            "/api/v1/evaluations/1/sprint-tests",
            json=mock_sprint_test_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["distance_meters"] == 30


@pytest.mark.asyncio
async def test_add_sprint_test_athlete_not_found(admin_client):
    """POST /evaluations/{id}/sprint-tests debe validar atleta."""
    with patch(
        "app.services.routers.evaluation_router.sprint_test_controller"
    ) as mock_controller:
        from app.utils.exceptions import DatabaseException

        mock_controller.add_test.side_effect = DatabaseException("Atleta 999 no existe")

        response = await admin_client.post(
            "/api/v1/evaluations/1/sprint-tests",
            json={
                "athlete_id": 999,
                "date": datetime.now().isoformat(),
                "evaluation_id": 1,
                "distance_meters": 30,
                "time_0_10_s": 1.85,
                "time_0_30_s": 3.95,
            },
        )

        assert response.status_code == 400


# ==============================================
# TESTS: POST /evaluations/{id}/yoyo-tests
# ==============================================


@pytest.mark.asyncio
async def test_add_yoyo_test_success(admin_client, mock_yoyo_test_data):
    """POST /evaluations/{id}/yoyo-tests debe agregar un Yoyo Test."""
    with patch(
        "app.services.routers.evaluation_router.yoyo_test_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 2
        mock_test.type = "yoyo_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.shuttle_count = 47
        mock_test.final_level = "18.2"
        mock_test.failures = 2
        mock_test.observations = None
        mock_controller.add_test.return_value = mock_test

        response = await admin_client.post(
            "/api/v1/evaluations/1/yoyo-tests",
            json=mock_yoyo_test_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["shuttle_count"] == 47


# ==============================================
# TESTS: POST /evaluations/{id}/endurance-tests
# ==============================================


@pytest.mark.asyncio
async def test_add_endurance_test_success(admin_client, mock_endurance_test_data):
    """POST /evaluations/{id}/endurance-tests debe agregar un Endurance Test."""
    with patch(
        "app.services.routers.evaluation_router.endurance_test_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 3
        mock_test.type = "endurance_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.min_duration = 12
        mock_test.total_distance_m = 2500
        mock_test.observations = None
        mock_controller.add_test.return_value = mock_test

        response = await admin_client.post(
            "/api/v1/evaluations/1/endurance-tests",
            json=mock_endurance_test_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["min_duration"] == 12


# ==============================================
# TESTS: POST /evaluations/{id}/technical-assessments
# ==============================================


@pytest.mark.asyncio
async def test_add_technical_assessment_success(
    admin_client, mock_technical_assessment_data
):
    """POST /evaluations/{id}/technical-assessments debe agregar
    Technical Assessment."""
    with patch(
        "app.services.routers.evaluation_router.technical_assessment_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 4
        mock_test.type = "technical_assessment"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.ball_control = "MUY_ALTO"
        mock_test.short_pass = "ALTO"
        mock_test.long_pass = "MEDIO"
        mock_test.shooting = "ALTO"
        mock_test.dribbling = "MUY_ALTO"
        mock_test.observations = None
        mock_controller.add_test.return_value = mock_test

        response = await admin_client.post(
            "/api/v1/evaluations/1/technical-assessments",
            json=mock_technical_assessment_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["ball_control"] == "MUY_ALTO"


# ==============================================
# TESTS: GET /evaluations/{id}/tests
# ==============================================


@pytest.mark.asyncio
async def test_list_evaluation_tests_success(admin_client):
    """GET /evaluations/{id}/tests debe listar tests de una evaluación."""
    with patch(
        "app.services.routers.evaluation_router.test_controller"
    ) as mock_controller:
        mock_test = MagicMock()
        mock_test.id = 1
        mock_test.type = "sprint_test"
        mock_test.date = datetime.now()
        mock_test.athlete_id = 5
        mock_test.evaluation_id = 1
        mock_test.observations = "Good performance"

        mock_controller.list_tests_by_evaluation.return_value = [mock_test]

        response = await admin_client.get("/api/v1/evaluations/1/tests")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1


@pytest.mark.asyncio
async def test_list_evaluation_tests_empty(admin_client):
    """GET /evaluations/{id}/tests debe retornar lista vacía."""
    with patch(
        "app.services.routers.evaluation_router.test_controller"
    ) as mock_controller:
        mock_controller.list_tests_by_evaluation.return_value = []

        response = await admin_client.get("/api/v1/evaluations/1/tests")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 0


# ==============================================
# TESTS: DELETE /evaluations/tests/{test_id}
# ==============================================


@pytest.mark.asyncio
async def test_delete_test_success(admin_client):
    """DELETE /evaluations/tests/{id} debe eliminar un test."""
    with patch(
        "app.services.routers.evaluation_router.test_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = True

        response = await admin_client.delete("/api/v1/evaluations/tests/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Test eliminado correctamente"


@pytest.mark.asyncio
async def test_delete_test_not_found(admin_client):
    """DELETE /evaluations/tests/{id} debe retornar 404 si no existe."""
    with patch(
        "app.services.routers.evaluation_router.test_controller"
    ) as mock_controller:
        mock_controller.delete_test.return_value = False

        response = await admin_client.delete("/api/v1/evaluations/tests/999")

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
