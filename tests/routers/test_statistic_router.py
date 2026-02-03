"""Tests para statistic_router."""

from unittest.mock import patch

import pytest

from app.utils.exceptions import AppException


class TestStatisticRouter:
    """Tests para endpoints de estadísticas."""

    # ==============================================
    # TESTS: GET /statistics/overview
    # ==============================================

    @pytest.mark.asyncio
    async def test_get_club_overview_success(self, coach_client):
        """Obtiene resumen del club exitosamente."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_club_overview.return_value = {
                "total_athletes": 50,
                "by_type": {"UNL": 30, "MINOR": 20},
            }

            response = await coach_client.get("/api/v1/statistics/overview")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["total_athletes"] == 50

    @pytest.mark.asyncio
    async def test_get_club_overview_with_filters(self, coach_client):
        """Obtiene resumen del club con filtros."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_club_overview.return_value = {
                "total_athletes": 15,
            }

            response = await coach_client.get(
                "/api/v1/statistics/overview?type_athlete=UNL&sex=MALE"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_club_overview_app_exception(self, coach_client):
        """Maneja AppException en overview."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_club_overview.side_effect = AppException(
                status_code=400, message="Error en consulta"
            )

            response = await coach_client.get("/api/v1/statistics/overview")

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_club_overview_unexpected_exception(self, coach_client):
        """Maneja excepción inesperada en overview."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_club_overview.side_effect = Exception(
                "Error inesperado"
            )

            response = await coach_client.get("/api/v1/statistics/overview")

            assert response.status_code == 500

    # ==============================================
    # TESTS: GET /statistics/attendance
    # ==============================================

    @pytest.mark.asyncio
    async def test_get_attendance_statistics_success(self, coach_client):
        """Obtiene estadísticas de asistencia exitosamente."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_attendance_statistics.return_value = {
                "total_records": 100,
                "attendance_rate": 85.5,
            }

            response = await coach_client.get("/api/v1/statistics/attendance")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["attendance_rate"] == 85.5

    @pytest.mark.asyncio
    async def test_get_attendance_statistics_with_date_range(self, coach_client):
        """Obtiene estadísticas de asistencia con rango de fechas."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_attendance_statistics.return_value = {}

            response = await coach_client.get(
                "/api/v1/statistics/attendance?start_date=2024-01-01&end_date=2024-12-31"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_attendance_statistics_app_exception(self, coach_client):
        """Maneja AppException en attendance."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_attendance_statistics.side_effect = AppException(
                status_code=400, message="Error"
            )

            response = await coach_client.get("/api/v1/statistics/attendance")

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_attendance_statistics_unexpected_exception(self, coach_client):
        """Maneja excepción inesperada en attendance."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_attendance_statistics.side_effect = Exception("Error")

            response = await coach_client.get("/api/v1/statistics/attendance")

            assert response.status_code == 500

    # ==============================================
    # TESTS: GET /statistics/tests
    # ==============================================

    @pytest.mark.asyncio
    async def test_get_test_performance_success(self, coach_client):
        """Obtiene estadísticas de tests exitosamente."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_test_performance.return_value = {
                "total_tests": 200,
                "by_type": {"sprint": 50, "endurance": 75, "yoyo": 75},
            }

            response = await coach_client.get("/api/v1/statistics/tests")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["total_tests"] == 200

    @pytest.mark.asyncio
    async def test_get_test_performance_with_filters(self, coach_client):
        """Obtiene estadísticas de tests con filtros."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_test_performance.return_value = {}

            response = await coach_client.get(
                "/api/v1/statistics/tests?start_date=2024-01-01&type_athlete=UNL"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_test_performance_app_exception(self, coach_client):
        """Maneja AppException en test performance."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_test_performance.side_effect = AppException(
                status_code=400, message="Error"
            )

            response = await coach_client.get("/api/v1/statistics/tests")

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_test_performance_unexpected_exception(self, coach_client):
        """Maneja excepción inesperada en test performance."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_test_performance.side_effect = Exception("Error")

            response = await coach_client.get("/api/v1/statistics/tests")

            assert response.status_code == 500

    # ==============================================
    # TESTS: GET /statistics/athlete/{athlete_id}
    # ==============================================

    @pytest.mark.asyncio
    async def test_get_athlete_individual_stats_success(self, coach_client):
        """Obtiene estadísticas individuales de atleta."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_athlete_individual_stats.return_value = {
                "athlete_id": 1,
                "name": "Juan Pérez",
                "total_tests": 10,
            }

            response = await coach_client.get("/api/v1/statistics/athlete/1")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["athlete_id"] == 1

    @pytest.mark.asyncio
    async def test_get_athlete_individual_stats_not_found(self, coach_client):
        """Retorna 404 si el atleta no existe."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_athlete_individual_stats.return_value = None

            response = await coach_client.get("/api/v1/statistics/athlete/999")

            assert response.status_code == 404
            data = response.json()
            assert data["status"] == "error"
            assert "no encontrado" in data["message"]

    @pytest.mark.asyncio
    async def test_get_athlete_individual_stats_app_exception(self, coach_client):
        """Maneja AppException en athlete stats."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_athlete_individual_stats.side_effect = AppException(
                status_code=400, message="Error"
            )

            response = await coach_client.get("/api/v1/statistics/athlete/1")

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_athlete_individual_stats_unexpected_exception(
        self, coach_client
    ):
        """Maneja excepción inesperada en athlete stats."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.get_athlete_individual_stats.side_effect = Exception(
                "Error"
            )

            response = await coach_client.get("/api/v1/statistics/athlete/1")

            assert response.status_code == 500

    # ==============================================
    # TESTS: PATCH /statistics/athlete/{athlete_id}/sports-stats
    # ==============================================

    @pytest.mark.asyncio
    async def test_update_sports_stats_success(self, coach_client):
        """Actualiza estadísticas deportivas exitosamente."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.update_sports_stats.return_value = {
                "athlete_id": 1,
                "matches_played": 10,
            }

            payload = {"matches_played": 10, "goals": 5}
            response = await coach_client.patch(
                "/api/v1/statistics/athlete/1/sports-stats", json=payload
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_update_sports_stats_not_found(self, coach_client):
        """Retorna 404 si el atleta no existe."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.update_sports_stats.return_value = None

            payload = {"matches_played": 10}
            response = await coach_client.patch(
                "/api/v1/statistics/athlete/999/sports-stats", json=payload
            )

            assert response.status_code == 404
            data = response.json()
            assert data["status"] == "error"

    @pytest.mark.asyncio
    async def test_update_sports_stats_app_exception(self, coach_client):
        """Maneja AppException en update sports stats."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.update_sports_stats.side_effect = AppException(
                status_code=400, message="Error"
            )

            payload = {"matches_played": 10}
            response = await coach_client.patch(
                "/api/v1/statistics/athlete/1/sports-stats", json=payload
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_sports_stats_unexpected_exception(self, coach_client):
        """Maneja excepción inesperada en update sports stats."""
        with patch(
            "app.services.routers.statistic_router.statistic_controller"
        ) as mock_controller:
            mock_controller.update_sports_stats.side_effect = Exception("Error")

            payload = {"matches_played": 10}
            response = await coach_client.patch(
                "/api/v1/statistics/athlete/1/sports-stats", json=payload
            )

            assert response.status_code == 500
