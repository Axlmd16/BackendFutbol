"""Tests de integración para los endpoints de asistencia.

Nota: Los tests de lógica de negocio están cubiertos en test_attendance_controller.py
y test_attendance_dao.py. Estos tests cubren principalmente validaciones de entrada
y autenticación a nivel de router.
"""

import pytest

# ==============================================
# TESTS: VALIDACIÓN DE ENTRADA POST /attendances/bulk
# ==============================================


@pytest.mark.asyncio
async def test_create_bulk_attendance_empty_records(admin_client):
    """Intentar crear asistencia con lista vacía de registros."""
    response = await admin_client.post(
        "/api/v1/attendances/bulk",
        json={
            "date": "2025-12-30",
            "time": "10:30",
            "records": [],
        },
    )

    # Lista vacía ahora es válida (limpia asistencias)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_bulk_attendance_invalid_time_format(admin_client):
    """Intentar crear asistencia con hora inválida."""
    response = await admin_client.post(
        "/api/v1/attendances/bulk",
        json={
            "date": "2025-12-30",
            "time": "25:00",  # Hora inválida
            "records": [{"athlete_id": 1, "is_present": True}],
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_bulk_attendance_invalid_date_format(admin_client):
    """Intentar crear asistencia con fecha inválida."""
    response = await admin_client.post(
        "/api/v1/attendances/bulk",
        json={
            "date": "invalid-date",
            "time": "10:30",
            "records": [{"athlete_id": 1, "is_present": True}],
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_bulk_attendance_without_auth(client):
    """Intentar crear asistencia sin autenticación."""
    response = await client.post(
        "/api/v1/attendances/bulk",
        json={
            "date": "2025-12-30",
            "time": "10:30",
            "records": [{"athlete_id": 1, "is_present": True}],
        },
    )

    # Sin autenticación debe fallar
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_bulk_attendance_missing_date(admin_client):
    """Intentar crear asistencia sin fecha."""
    response = await admin_client.post(
        "/api/v1/attendances/bulk",
        json={
            "time": "10:30",
            "records": [{"athlete_id": 1, "is_present": True}],
        },
    )

    # Fecha es requerida
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_bulk_attendance_missing_records(admin_client):
    """Intentar crear asistencia sin records."""
    response = await admin_client.post(
        "/api/v1/attendances/bulk",
        json={
            "date": "2025-12-30",
            "time": "10:30",
        },
    )

    # Records es requerido
    assert response.status_code == 422


# ==============================================
# TESTS: VALIDACIÓN DE ENTRADA GET /attendances/by-date
# ==============================================


@pytest.mark.asyncio
async def test_get_attendances_missing_date(admin_client):
    """Obtener asistencias sin fecha (parámetro requerido)."""
    response = await admin_client.get("/api/v1/attendances/by-date")

    # Fecha es requerida
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_attendances_invalid_date_format(admin_client):
    """Obtener asistencias con fecha inválida."""
    response = await admin_client.get(
        "/api/v1/attendances/by-date",
        params={"date": "invalid-date"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_attendances_without_auth(client):
    """Obtener asistencias sin autenticación."""
    response = await client.get(
        "/api/v1/attendances/by-date",
        params={"date": "2025-12-30"},
    )

    # Sin autenticación debe fallar
    assert response.status_code == 401


# ==============================================
# TESTS: VALIDACIÓN DE ENTRADA GET /attendances/summary
# ==============================================


@pytest.mark.asyncio
async def test_get_summary_missing_date(admin_client):
    """Obtener resumen sin fecha (parámetro requerido)."""
    response = await admin_client.get("/api/v1/attendances/summary")

    # Fecha es requerida
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_summary_without_auth(client):
    """Obtener resumen sin autenticación."""
    response = await client.get(
        "/api/v1/attendances/summary",
        params={"date": "2025-12-30"},
    )

    # Sin autenticación debe fallar
    assert response.status_code == 401
