"""Tests para el controlador de reportes."""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch

from app.controllers.report_controller import ReportController
from app.schemas.report_schema import ReportFilter
from app.utils.exceptions import ValidationException


class TestReportController:
    """Tests del controlador de reportes."""

    def setup_method(self):
        """Configuración para cada test."""
        self.controller = ReportController()

    def test_validate_filters_invalid_date_range(self):
        """Verifica que se valide correctamente el rango de fechas."""
        filters = ReportFilter(
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 1),
            format="csv",
        )

        with pytest.raises(ValidationException) as exc_info:
            self.controller.validate_filters(filters)

        assert "start_date debe ser menor o igual a end_date" in str(exc_info.value)

    def test_validate_filters_no_inclusion_filters(self):
        """Verifica que al menos un filtro de inclusión esté activo."""
        filters = ReportFilter(
            format="csv",
            include_attendance=False,
            include_evaluations=False,
            include_tests=False,
        )

        with pytest.raises(ValidationException) as exc_info:
            self.controller.validate_filters(filters)

        assert "Al menos uno de los filtros de inclusión debe estar activo" in str(
            exc_info.value
        )

    def test_validate_filters_valid(self):
        """Verifica que filters válidos no levanten excepciones."""
        filters = ReportFilter(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 15),
            format="csv",
            include_attendance=True,
        )

        # No debe lanzar excepción
        self.controller.validate_filters(filters)

    def test_generate_csv_report_basic(self):
        """Verifica la generación básica de reporte CSV."""
        from app.models.athlete import Athlete

        # Mock de datos
        athlete = Mock(spec=Athlete)
        athlete.id = 1
        athlete.full_name = "Test Athlete"

        report_data = {
            "athletes": [athlete],
            "attendance": [],
            "evaluations": [],
            "tests": {
                "sprint": [],
                "endurance": [],
                "yoyo": [],
                "technical": [],
            },
            "statistics": {
                "total_attendance": 0,
                "total_evaluations": 0,
                "total_tests": 0,
            },
        }

        filters = ReportFilter(format="csv")

        result = self.controller.generate_csv_report(report_data, filters)

        assert result is not None
        content = result.getvalue()
        assert b"REPORTE DEPORTIVO" in content
        assert b"Total de Atletas: 1" in content

    @patch("app.controllers.report_controller.openpyxl")
    def test_generate_xlsx_report_basic(self, mock_openpyxl):
        """Verifica la generación básica de reporte XLSX."""
        from app.models.athlete import Athlete

        # Mock de datos
        athlete = Mock(spec=Athlete)
        athlete.id = 1
        athlete.full_name = "Test Athlete"

        report_data = {
            "athletes": [athlete],
            "attendance": [],
            "evaluations": [],
            "tests": {
                "sprint": [],
                "endurance": [],
                "yoyo": [],
                "technical": [],
            },
            "statistics": {
                "total_attendance": 0,
                "total_evaluations": 0,
                "total_tests": 0,
            },
        }

        filters = ReportFilter(format="xlsx")

        # Mock openpyxl si no está disponible
        if mock_openpyxl:
            mock_workbook = Mock()
            mock_openpyxl.Workbook.return_value = mock_workbook

        result = self.controller.generate_xlsx_report(report_data, filters)

        assert result is not None

    def test_generate_report_invalid_format(self):
        """Verifica que un formato inválido lance excepción."""
        filters = ReportFilter(format="invalid_format")

        with pytest.raises(ValidationException):
            self.controller.generate_report(
                db=Mock(),
                filters=filters,
                user_dni="1234567890",
            )
