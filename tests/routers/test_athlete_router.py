import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_register_athlete_endpoint_success(client):
    with patch("app.services.routers.inscription_router.athlete_controller") as mock_controller:
        mock_result = MagicMock(
            athlete_id=1,
            statistic_id=10,
            first_name="Juan",
            last_name="Pérez",
            institutional_email="juan.perez@unl.edu.ar",
        )
        mock_result.model_dump = MagicMock(return_value={
            "athlete_id": 1,
            "statistic_id": 10,
            "first_name": "Juan",
            "last_name": "Pérez",
            "institutional_email": "juan.perez@unl.edu.ar",
        })
        mock_controller.register_athlete_unl = MagicMock(return_value=mock_result)

        resp = await client.post("/api/v1/inscription/deportista", json={
            "first_name": "Juan",
            "last_name": "Pérez",
            "dni": "12345678",
            "phone": "3424123456",
            "birth_date": "1998-05-15",
            "institutional_email": "juan.perez@unl.edu.ar",
            "university_role": "student",
            "weight": "75.5",
            "height": "180",
        })

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["athlete_id"] == 1
        assert data["data"]["statistic_id"] == 10


@pytest.mark.asyncio
async def test_register_athlete_endpoint_rol_invalido(client):
    from app.utils.exceptions import ValidationException

    with patch("app.services.routers.inscription_router.athlete_controller") as mock_controller:    
        mock_controller.register_athlete_unl = MagicMock(
            side_effect=ValidationException("Rol inválido. Debe ser uno de: STUDENT, TEACHER, ADMIN, WORKER")
        )
        
        resp = await client.post("/api/v1/inscription/deportista", json={
            "first_name": "Ana",
            "last_name": "López",
            "dni": "12345678",
            "institutional_email": "ana@test.com",
            "university_role": "deportista",
        })

        # El router devuelve 400 en caso de rol inválido
        assert resp.status_code == 400
        body = resp.json()
        assert body.get("status") == "error"
        assert "Rol inválido" in (body.get("message") or body.get("detail", ""))


@pytest.mark.asyncio
async def test_register_athlete_endpoint_dni_duplicado(client):
    from app.utils.exceptions import AlreadyExistsException

    with patch("app.services.routers.inscription_router.athlete_controller") as mock_controller:    
        mock_controller.register_athlete_unl = MagicMock(
            side_effect=AlreadyExistsException("El DNI ya existe en el sistema.")
        )
        
        resp = await client.post("/api/v1/inscription/deportista", json={
            "first_name": "Luis",
            "last_name": "Martínez",
            "dni": "12345678",
            "institutional_email": "luis@test.com",
            "university_role": "student",
        })

        assert resp.status_code == 409
        body = resp.json()
        assert body.get("status") == "error"
        assert "DNI" in (body.get("message") or body.get("detail", ""))


@pytest.mark.asyncio
async def test_register_athlete_endpoint_email_duplicado(client):
    from app.utils.exceptions import AlreadyExistsException

    with patch("app.services.routers.inscription_router.athlete_controller") as mock_controller:    
        mock_controller.register_athlete_unl = MagicMock(
            side_effect=AlreadyExistsException("El email institucional ya existe en el sistema.")   
        )
        
        resp = await client.post("/api/v1/inscription/deportista", json={
            "first_name": "Roberto",
            "last_name": "Silva",
            "dni": "87654321",
            "institutional_email": "roberto@test.com",
            "university_role": "student",
        })

        assert resp.status_code == 409
        body = resp.json()
        assert body.get("status") == "error"
        assert "email" in (body.get("message", "") + body.get("detail", "")).lower()


@pytest.mark.asyncio
async def test_register_athlete_endpoint_validacion_formato(client):
    # Falta campo requerido (email), debería 422 con formato custom
    resp = await client.post("/api/v1/inscription/deportista", json={
        "first_name": "Test",
        "last_name": "User",
        "dni": "1234",
        "university_role": "student",
    })
    assert resp.status_code == 422
    body = resp.json()
    assert body.get("status") == "error" or "errors" in body
