from unittest.mock import AsyncMock, patch

import pytest

from app.utils.exceptions import AlreadyExistsException


@pytest.mark.asyncio
async def test_register_athlete_unl_success(client):
    """Prueba de registro exitoso de atleta UNL."""
    from app.schemas.athlete_schema import AthleteInscriptionResponseDTO

    with patch(
        "app.services.routers.athlete_router.athlete_controller"
    ) as mock_controller:
        mock_result = AthleteInscriptionResponseDTO(
            athlete_id=1,
            statistic_id=10,
            full_name="Juan Pérez",
            dni="1710034065",
        )
        mock_controller.register_athlete_unl = AsyncMock(return_value=mock_result)

        response = await client.post(
            "/api/v1/athletes/register-unl",
            json={
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "1710034065",
                "phone": "3424123456",
                "birth_date": "1998-05-15",
                "weight": 75.5,
                "height": 180.0,
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["athlete_id"] == 1
        assert body["data"]["statistic_id"] == 10
        assert body["data"]["full_name"] == "Juan Pérez"


@pytest.mark.asyncio
async def test_register_athlete_unl_dni_duplicado(client):
    """Prueba de registro con DNI duplicado."""
    with patch(
        "app.services.routers.athlete_router.athlete_controller"
    ) as mock_controller:
        mock_controller.register_athlete_unl = AsyncMock(
            side_effect=AlreadyExistsException("El DNI ya existe en el sistema.")
        )

        response = await client.post(
            "/api/v1/athletes/register-unl",
            json={
                "first_name": "Luis",
                "last_name": "Martínez",
                "dni": "1710034065",
                "phone": "3424123456",
                "birth_date": "1998-05-15",
                "weight": 70.0,
                "height": 175.0,
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert data["status"] == "error"
        assert "DNI" in data["message"]


@pytest.mark.asyncio
async def test_register_athlete_unl_invalid_dni_format(client):
    """Prueba de registro con DNI inválido."""
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "invalid",
            "phone": "3424123456",
            "birth_date": "1998-05-15",
            "weight": 70.0,
            "height": 175.0,
        },
    )

    # DNI inválido en la request causa validación de Pydantic (422)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_athlete_unl_missing_required_field(client):
    """Prueba con campo requerido faltante."""
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            # Falta dni
            "phone": "3424123456",
            "birth_date": "1998-05-15",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_athlete_unl_invalid_date_format(client):
    """Prueba de registro con fecha de nacimiento inválida."""
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "9999999999",
            "phone": "3424123456",
            "birth_date": "invalid-date",
            "weight": 70.0,
            "height": 175.0,
        },
    )

    # Fecha inválida en la request causa validación de Pydantic (422)
    assert response.status_code == 422
