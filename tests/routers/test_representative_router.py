"""Tests para el endpoint /athletes/register-minor y CRUD de representantes."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums.relationship import Relationship
from app.schemas.athlete_schema import MinorAthleteInscriptionResponseDTO
from app.schemas.representative_schema import (
    RepresentativeInscriptionResponseDTO,
    RepresentativeResponse,
)
from app.utils.exceptions import AlreadyExistsException


def _mock_representative(**kwargs):
    """Crea un objeto simple con atributos de representante para tests."""
    defaults = dict(
        id=1,
        full_name="Juan Pérez",
        dni="1710034065",
        phone="0999123456",
        email="juan@test.com",
        external_person_id="ext-123",
        relationship_type=Relationship.FATHER,
        is_active=True,
        created_at=SimpleNamespace(isoformat=lambda: "2025-01-01T00:00:00"),
        updated_at=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ==========================================
# Tests para /athletes/register-minor (público)


@pytest.mark.asyncio
async def test_register_minor_athlete_success(client):
    """Prueba de registro exitoso de atleta menor con representante nuevo."""
    with patch(
        "app.services.routers.athlete_router.athlete_controller"
    ) as mock_controller:
        mock_result = MinorAthleteInscriptionResponseDTO(
            representative_id=1,
            representative_full_name="Juan Pérez",
            representative_dni="1710034065",
            representative_is_new=True,
            athlete_id=5,
            athlete_full_name="Carlos Pérez",
            athlete_dni="1700000142",
            statistic_id=5,
        )
        mock_controller.register_minor_athlete = AsyncMock(return_value=mock_result)

        response = await client.post(
            "/api/v1/athletes/register-minor",
            json={
                "representative": {
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "dni": "1710034065",
                    "phone": "0999123456",
                    "email": "juan@test.com",
                    "relationship_type": "FATHER",
                },
                "athlete": {
                    "first_name": "Carlos",
                    "last_name": "Pérez",
                    "dni": "1700000142",
                    "birth_date": "2012-05-15",
                    "sex": "MALE",
                    "height": 1.45,
                    "weight": 38.5,
                },
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["representative_id"] == 1
        assert body["data"]["representative_is_new"] is True
        assert body["data"]["athlete_id"] == 5
        assert body["data"]["athlete_full_name"] == "Carlos Pérez"


@pytest.mark.asyncio
async def test_register_minor_athlete_existing_representative(client):
    """Prueba con representante ya existente."""
    with patch(
        "app.services.routers.athlete_router.athlete_controller"
    ) as mock_controller:
        mock_result = MinorAthleteInscriptionResponseDTO(
            representative_id=1,
            representative_full_name="Juan Pérez",
            representative_dni="1710034065",
            representative_is_new=False,  # Ya existía
            athlete_id=6,
            athlete_full_name="María Pérez",
            athlete_dni="1700000159",
            statistic_id=6,
        )
        mock_controller.register_minor_athlete = AsyncMock(return_value=mock_result)

        response = await client.post(
            "/api/v1/athletes/register-minor",
            json={
                "representative": {
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "dni": "1710034065",
                    "relationship_type": "FATHER",
                },
                "athlete": {
                    "first_name": "María",
                    "last_name": "Pérez",
                    "dni": "1700000159",
                    "birth_date": "2014-03-20",
                    "sex": "FEMALE",
                },
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["data"]["representative_is_new"] is False


@pytest.mark.asyncio
async def test_register_minor_athlete_duplicate_athlete_dni(client):
    """Prueba con DNI de atleta duplicado."""
    with patch(
        "app.services.routers.athlete_router.athlete_controller"
    ) as mock_controller:
        mock_controller.register_minor_athlete = AsyncMock(
            side_effect=AlreadyExistsException(
                "Ya existe un deportista con ese DNI en el club."
            )
        )

        response = await client.post(
            "/api/v1/athletes/register-minor",
            json={
                "representative": {
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "dni": "1710034065",
                    "relationship_type": "FATHER",
                },
                "athlete": {
                    "first_name": "Carlos",
                    "last_name": "Pérez",
                    "dni": "1700000142",
                    "birth_date": "2012-05-15",
                    "sex": "MALE",
                },
            },
        )

        assert response.status_code == 409
        body = response.json()
        # HTTPException devuelve "detail", pero verificamos ambos casos
        error_msg = body.get("detail", body.get("message", ""))
        assert "DNI" in error_msg or "deportista" in error_msg.lower()


@pytest.mark.asyncio
async def test_register_minor_athlete_missing_birth_date(client):
    """Prueba con fecha de nacimiento faltante."""
    response = await client.post(
        "/api/v1/athletes/register-minor",
        json={
            "representative": {
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "1710034065",
                "relationship_type": "FATHER",
            },
            "athlete": {
                "first_name": "Carlos",
                "last_name": "Pérez",
                "dni": "1234567891",
                # Falta birth_date - requerido para menores
                "sex": "MALE",
            },
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_minor_athlete_missing_relationship_type(client):
    """Prueba sin tipo de relación."""
    response = await client.post(
        "/api/v1/athletes/register-minor",
        json={
            "representative": {
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "1710034065",
                # Falta relationship_type
            },
            "athlete": {
                "first_name": "Carlos",
                "last_name": "Pérez",
                "dni": "1234567891",
                "birth_date": "2012-05-15",
                "sex": "MALE",
            },
        },
    )

    assert response.status_code == 422


# ==========================================
# Tests para /representatives/by-dni (público)


@pytest.mark.asyncio
async def test_get_representative_by_dni_found(client):
    """Prueba de búsqueda de representante por DNI encontrado."""
    with patch(
        "app.services.routers.representative_router.representative_controller"
    ) as mock_controller:
        mock_result = RepresentativeResponse(
            id=1,
            full_name="Juan Pérez",
            dni="1710034065",
            phone="0999123456",
            relationship_type="Father",
            is_active=True,
            created_at="2025-01-01T00:00:00",
        )
        mock_controller.get_representative_by_dni = MagicMock(return_value=mock_result)

        response = await client.get("/api/v1/representatives/by-dni/1710034065")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["id"] == 1
        assert body["data"]["full_name"] == "Juan Pérez"


@pytest.mark.asyncio
async def test_get_representative_by_dni_not_found(client):
    """Prueba de búsqueda de representante por DNI no encontrado."""
    with patch(
        "app.services.routers.representative_router.representative_controller"
    ) as mock_controller:
        mock_controller.get_representative_by_dni = MagicMock(return_value=None)

        response = await client.get("/api/v1/representatives/by-dni/9999999999")

        assert response.status_code == 404
        body = response.json()
        assert body["status"] == "error"


# ==========================================
# Tests para /representatives (autenticados)


@pytest.mark.asyncio
async def test_create_representative_success(admin_client):
    """Prueba de creación de representante por admin."""
    with patch(
        "app.services.routers.representative_router.representative_controller"
    ) as mock_controller:
        mock_result = RepresentativeInscriptionResponseDTO(
            representative_id=1,
            full_name="Juan Pérez",
            dni="1710034065",
            relationship_type="Father",
        )
        mock_controller.create_representative = AsyncMock(return_value=mock_result)

        response = await admin_client.post(
            "/api/v1/representatives/create",
            json={
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "1710034065",
                "phone": "0999123456",
                "email": "juan@test.com",
                "relationship_type": "FATHER",
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["representative_id"] == 1


@pytest.mark.asyncio
async def test_create_representative_duplicate_dni(admin_client):
    """Prueba de creación con DNI duplicado."""
    with patch(
        "app.services.routers.representative_router.representative_controller"
    ) as mock_controller:
        mock_controller.create_representative = AsyncMock(
            side_effect=AlreadyExistsException(
                "Ya existe un representante con ese DNI."
            )
        )

        response = await admin_client.post(
            "/api/v1/representatives/create",
            json={
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "1710034065",
                "relationship_type": "FATHER",
            },
        )

        assert response.status_code == 409


@pytest.mark.asyncio
async def test_deactivate_representative_success(admin_client):
    """Prueba de desactivación de representante."""
    with patch(
        "app.services.routers.representative_router.representative_controller"
    ) as mock_controller:
        mock_controller.deactivate_representative = MagicMock(return_value=None)

        response = await admin_client.patch("/api/v1/representatives/deactivate/1")

        assert response.status_code == 200
        body = response.json()
        assert "desactivado" in body["message"].lower()


@pytest.mark.asyncio
async def test_activate_representative_success(admin_client):
    """Prueba de activación de representante."""
    with patch(
        "app.services.routers.representative_router.representative_controller"
    ) as mock_controller:
        mock_controller.activate_representative = MagicMock(return_value=None)

        response = await admin_client.patch("/api/v1/representatives/activate/1")

        assert response.status_code == 200
        body = response.json()
        assert "activado" in body["message"].lower()
