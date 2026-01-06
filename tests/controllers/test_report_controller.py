"""Tests para el controlador de reportes."""

from datetime import date
from io import BytesIO
from unittest.mock import Mock, patch

import pytest

from app.controllers.report_controller import ReportController
from app.schemas.report_schema import ReportFilter, ReportType
from app.utils.exceptions import ValidationException


class TestReportController:
    """Tests del controlador de reportes."""

    def setup_method(self):
        """Configuración para cada test."""
        self.controller = ReportController()
        self.mock_db = Mock()

    def test_generate_report_attendance_pdf(self):
        """Verifica generación de reporte de asistencia en PDF."""
        filters = ReportFilter(
            report_type=ReportType.ATTENDANCE,
            format="pdf",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )

        with patch.object(
            self.controller.report_service,
            "generate_attendance_report",
            return_value=BytesIO(b"PDF content"),
        ) as mock_generate:
            result = self.controller.generate_report(
                db=self.mock_db, filters=filters, user_name="Test User"
            )

            assert result is not None
            assert isinstance(result, BytesIO)
            mock_generate.assert_called_once()

    def test_generate_report_tests_csv(self):
        """Verifica generación de reporte de tests en CSV."""
        filters = ReportFilter(
            report_type=ReportType.TESTS,
            format="csv",
        )

        with patch.object(
            self.controller.report_service,
            "generate_tests_report",
            return_value=BytesIO(b"CSV content"),
        ) as mock_generate:
            result = self.controller.generate_report(
                db=self.mock_db, filters=filters, user_name="Test User"
            )

            assert result is not None
            mock_generate.assert_called_once_with(
                db=self.mock_db, filters=filters, user_name="Test User"
            )

    def test_generate_report_statistics_xlsx(self):
        """Verifica generación de reporte de estadísticas en XLSX."""
        filters = ReportFilter(
            report_type=ReportType.STATISTICS,
            format="xlsx",
        )

        with patch.object(
            self.controller.report_service,
            "generate_statistics_report",
            return_value=BytesIO(b"XLSX content"),
        ) as mock_generate:
            result = self.controller.generate_report(
                db=self.mock_db, filters=filters, user_name="Test User"
            )

            assert result is not None
            mock_generate.assert_called_once()

    def test_generate_report_no_type(self):
        """Verifica que falle si no se especifica tipo de reporte."""
        filters = ReportFilter(format="pdf")

        with pytest.raises(ValidationException) as exc_info:
            self.controller.generate_report(
                db=self.mock_db, filters=filters, user_name="Test User"
            )

        assert "tipo de reporte" in str(exc_info.value).lower()

    def test_generate_report_with_filters(self):
        """Verifica que los filtros se pasen correctamente."""
        from app.schemas.athlete_schema import SexInput
        from app.schemas.user_schema import TypeStament

        filters = ReportFilter(
            report_type=ReportType.ATTENDANCE,
            format="pdf",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            athlete_type=TypeStament.EXTERNOS,
            sex=SexInput.MALE,
        )

        with patch.object(
            self.controller.report_service,
            "generate_attendance_report",
            return_value=BytesIO(b"PDF with filters"),
        ) as mock_generate:
            self.controller.generate_report(
                db=self.mock_db, filters=filters, user_name="Test User"
            )

            # Verificar que se llamó con los filtros correctos
            call_args = mock_generate.call_args
            assert call_args[1]["filters"] == filters

    def test_generate_report_with_athlete_id(self):
        """Verifica generación de reporte individual (con athlete_id)."""
        filters = ReportFilter(
            report_type=ReportType.ATTENDANCE,
            format="pdf",
            athlete_id=123,
        )

        with patch.object(
            self.controller.report_service,
            "generate_attendance_report",
            return_value=BytesIO(b"Individual report"),
        ) as mock_generate:
            result = self.controller.generate_report(
                db=self.mock_db, filters=filters, user_name="Test User"
            )

            assert result is not None
            # Verificar que athlete_id se pasó
            call_args = mock_generate.call_args
            assert call_args[1]["filters"].athlete_id == 123

    def test_generate_report_invalid_format(self):
        """Verifica que un formato inválido lance excepción Pydantic."""
        from pydantic_core import ValidationError

        with pytest.raises(ValidationError):
            ReportFilter(report_type=ReportType.ATTENDANCE, format="invalid_format")

    def test_generate_report_service_exception(self):
        """Verifica manejo de excepciones del servicio de reportes."""
        filters = ReportFilter(
            report_type=ReportType.ATTENDANCE,
            format="pdf",
        )

        with patch.object(
            self.controller.report_service,
            "generate_attendance_report",
            side_effect=Exception("Service error"),
        ):
            with pytest.raises(ValidationException) as exc_info:
                self.controller.generate_report(
                    db=self.mock_db, filters=filters, user_name="Test User"
                )

            assert "error al generar reporte" in str(exc_info.value).lower()
