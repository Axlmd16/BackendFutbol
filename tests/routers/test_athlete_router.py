from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.utils.exceptions import AlreadyExistsException


def _mock_athlete(**kwargs):
    """Crea un objeto simple con atributos de atleta para tests."""
    defaults = dict(
        id=1,
        full_name="Juan Pérez",
        dni="1710034065",
        type_athlete="UNL",
        sex=SimpleNamespace(value="MALE"),
        is_active=True,
        external_person_id="ext-123",
        date_of_birth=None,
        height=180.0,
        weight=75.0,
        created_at=SimpleNamespace(isoformat=lambda: "2025-01-01T00:00:00"),
        updated_at=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


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
                "phone": "0999123456",
                "direction": "Av. Principal 123",
                "type_identification": "CEDULA",
                "type_stament": "ESTUDIANTES",
                "birth_date": "1998-05-15",
                "sex": "MALE",
                "weight": 75.5,
                "height": 1.80,
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["athlete_id"] == 1
        assert body["data"]["statistic_id"] == 10
        assert body["data"]["full_name"] == "Juan Pérez"

    @pytest.mark.asyncio
    async def test_get_all_athletes_success(admin_client):
        """Lista de atletas con filtros y paginación OK."""
        with patch(
            "app.services.routers.athlete_router.athlete_controller"
        ) as mock_controller:
            mock_items = [_mock_athlete(id=1), _mock_athlete(id=2, full_name="Ana")]
            mock_controller.get_all_athletes.return_value = (mock_items, 2)

            resp = await admin_client.get(
                "/api/v1/athletes/all",
                params={
                    "search": "Juan",
                    "type_athlete": "UNL",
                    "sex": "MALE",
                    "is_active": True,
                    "page": 1,
                    "limit": 10,
                },
            )
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["total"] == 2
            assert len(data["items"]) == 2
            assert data["page"] == 1 and data["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_athlete_by_id_found(admin_client):
        """Detalle de atleta encontrado."""
        with patch(
            "app.services.routers.athlete_router.athlete_controller"
        ) as mock_controller:
            mock_controller.get_athlete_by_id.return_value = _mock_athlete(id=3)

            resp = await admin_client.get("/api/v1/athletes/3")
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["id"] == 3
            assert body["data"]["dni"] == "1710034065"

    @pytest.mark.asyncio
    async def test_get_athlete_by_id_not_found(admin_client):
        """Detalle de atleta no encontrado."""
        with patch(
            "app.services.routers.athlete_router.athlete_controller"
        ) as mock_controller:
            mock_controller.get_athlete_by_id.return_value = None

            resp = await admin_client.get("/api/v1/athletes/999")
            assert resp.status_code == 404
            assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_update_athlete_success(admin_client):
        """Actualización de datos básicos exitosa."""
        with patch(
            "app.services.routers.athlete_router.athlete_controller"
        ) as mock_controller:
            updated = _mock_athlete(height=182.0, weight=76.0)
            mock_controller.update_athlete.return_value = updated

            resp = await admin_client.put(
                "/api/v1/athletes/update/1",
                json={"height": 182.0, "weight": 76.0},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["height"] == 182.0
            assert body["data"]["weight"] == 76.0

    @pytest.mark.asyncio
    async def test_update_athlete_not_found(admin_client):
        """Actualización cuando atleta no existe."""
        with patch(
            "app.services.routers.athlete_router.athlete_controller"
        ) as mock_controller:
            mock_controller.update_athlete.return_value = None

            resp = await admin_client.put(
                "/api/v1/athletes/update/999",
                json={"height": 170.0},
            )
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_desactivate_athlete_success(admin_client):
        """Desactivación exitosa (soft delete)."""
        with patch(
            "app.services.routers.athlete_router.athlete_controller"
        ) as mock_controller:
            mock_controller.desactivate_athlete.return_value = None

            resp = await admin_client.patch("/api/v1/athletes/desactivate/1")
            assert resp.status_code == 200
            assert resp.json()["message"].startswith("Atleta desactivado")

    @pytest.mark.asyncio
    async def test_activate_athlete_success(admin_client):
        """Activación exitosa (revierte soft delete)."""
        with patch(
            "app.services.routers.athlete_router.athlete_controller"
        ) as mock_controller:
            mock_controller.activate_athlete.return_value = None

            resp = await admin_client.patch("/api/v1/athletes/activate/1")
            assert resp.status_code == 200
            assert resp.json()["message"].startswith("Atleta activado")


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
                "phone": "0999123456",
                "direction": "Calle 456",
                "type_identification": "CEDULA",
                "type_stament": "ESTUDIANTES",
                "birth_date": "1998-05-15",
                "sex": "MALE",
                "weight": 70.0,
                "height": 1.75,
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
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "1998-05-15",
            "sex": "MALE",
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
            # Falta dni y otros campos requeridos
            "phone": "0999123456",
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
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "invalid-date",
            "sex": "MALE",
            "weight": 70.0,
            "height": 175.0,
        },
    )

    # Fecha inválida en la request causa validación de Pydantic (422)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_athlete_unl_height_out_of_range(client):
    """Prueba de registro con altura fuera del rango permitido (1m - 2.5m)."""
    # Altura menor a 1m
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "1998-05-15",
            "sex": "MALE",
            "weight": 70.0,
            "height": 0.5,  # Altura inválida: menor a 1m
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "height" in str(data).lower()

    # Altura mayor a 2.5m
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "1998-05-15",
            "sex": "MALE",
            "weight": 70.0,
            "height": 3.0,  # Altura inválida: mayor a 2.5m
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "height" in str(data).lower()


@pytest.mark.asyncio
async def test_register_athlete_unl_weight_out_of_range(client):
    """Prueba de registro con peso fuera del rango permitido (18kg - 200kg)."""
    # Peso menor a 18kg
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "1998-05-15",
            "sex": "MALE",
            "weight": 10.0,  # Peso inválido: menor a 18kg
            "height": 1.75,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "weight" in str(data).lower()

    # Peso mayor a 200kg
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "1998-05-15",
            "sex": "MALE",
            "weight": 250.0,  # Peso inválido: mayor a 200kg
            "height": 1.75,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "weight" in str(data).lower()


@pytest.mark.asyncio
async def test_register_athlete_unl_negative_height(client):
    """Prueba de registro con altura negativa."""
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "1998-05-15",
            "sex": "MALE",
            "weight": 70.0,
            "height": -1.5,  # Altura negativa
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "height" in str(data).lower()


@pytest.mark.asyncio
async def test_register_athlete_unl_negative_weight(client):
    """Prueba de registro con peso negativo."""
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "1998-05-15",
            "sex": "MALE",
            "weight": -50.0,  # Peso negativo
            "height": 1.75,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "weight" in str(data).lower()


@pytest.mark.asyncio
async def test_register_athlete_unl_underage(client):
    """Prueba de registro con atleta menor de 16 años."""
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "2015-05-15",  # Menor de 16 años
            "sex": "MALE",
            "weight": 50.0,
            "height": 1.60,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "16" in str(data) or "edad" in str(data).lower()


@pytest.mark.asyncio
async def test_register_athlete_unl_birth_date_today(client):
    """Prueba de registro con fecha de nacimiento igual a hoy."""
    from datetime import date

    today = date.today().isoformat()
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": today,  # Fecha de hoy
            "sex": "MALE",
            "weight": 70.0,
            "height": 1.75,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "hoy" in str(data).lower() or "futuro" in str(data).lower()


@pytest.mark.asyncio
async def test_register_athlete_unl_birth_date_future(client):
    """Prueba de registro con fecha de nacimiento en el futuro."""
    response = await client.post(
        "/api/v1/athletes/register-unl",
        json={
            "first_name": "Test",
            "last_name": "User",
            "dni": "1710034065",
            "phone": "0999123456",
            "direction": "Calle Test",
            "type_identification": "CEDULA",
            "type_stament": "ESTUDIANTES",
            "birth_date": "2030-05-15",  # Fecha futura
            "sex": "MALE",
            "weight": 70.0,
            "height": 1.75,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "hoy" in str(data).lower() or "futuro" in str(data).lower()
