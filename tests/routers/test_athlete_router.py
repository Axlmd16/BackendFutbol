from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_register_athlete_unl_success(client):
    """POST /athletes/register-unl debe registrar un atleta exitosamente."""
    from app.schemas.athlete_schema import AthleteInscriptionResponseDTO

    with patch(
        "app.services.routers.athlete_router.athlete_controller"
    ) as mock_controller:
        # Crear un objeto real de Pydantic para evitar problemas de validación
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
