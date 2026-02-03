"""Tests para ReportService."""

from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

from app.schemas.report_schema import ReportFilter


class TestReportServiceInit:
    """Tests para inicialización de ReportService."""

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_init(self, mock_env, mock_stat_ctrl):
        """Verifica inicialización correcta."""
        from app.services.report_service import ReportService

        service = ReportService()

        assert service.statistic_controller is not None
        assert service.env is not None


class TestGenerateAttendanceReport:
    """Tests para generate_attendance_report."""

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_generate_attendance_report_csv(self, mock_env, mock_ctrl):
        """Genera reporte de asistencia en CSV."""
        from app.services.report_service import ReportService

        service = ReportService()
        service.statistic_controller = MagicMock()
        service.statistic_controller.get_attendance_statistics.return_value = {
            "total_records": 100,
            "total_present": 80,
            "total_absent": 20,
            "overall_attendance_rate": 80.0,
            "attendance_by_type": [],
        }

        mock_db = MagicMock()
        filters = ReportFilter(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), format="csv"
        )

        service._generate_tabular_report = MagicMock(return_value=BytesIO(b"csv data"))
        service._build_metadata = MagicMock()

        result = service.generate_attendance_report(mock_db, filters, "admin")

        assert isinstance(result, BytesIO)

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_generate_attendance_report_xlsx(self, mock_env, mock_ctrl):
        """Genera reporte de asistencia en Excel."""
        from app.services.report_service import ReportService

        service = ReportService()
        service.statistic_controller = MagicMock()
        service.statistic_controller.get_attendance_statistics.return_value = {
            "total_records": 100,
            "total_present": 80,
            "total_absent": 20,
            "overall_attendance_rate": 80.0,
            "attendance_by_type": [],
        }

        mock_db = MagicMock()
        filters = ReportFilter(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), format="xlsx"
        )

        service._generate_tabular_report = MagicMock(return_value=BytesIO(b"xlsx data"))
        service._build_metadata = MagicMock()

        result = service.generate_attendance_report(mock_db, filters, "admin")

        assert isinstance(result, BytesIO)

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_generate_attendance_report_pdf(self, mock_env, mock_ctrl):
        """Genera reporte de asistencia en PDF."""
        from app.services.report_service import ReportService

        service = ReportService()
        service.statistic_controller = MagicMock()
        service.statistic_controller.get_attendance_statistics.return_value = {
            "total_records": 100,
            "total_present": 80,
            "total_absent": 20,
            "overall_attendance_rate": 80.0,
            "attendance_by_type": [],
        }

        mock_db = MagicMock()
        filters = ReportFilter(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), format="pdf"
        )

        service._build_metadata = MagicMock()
        service._render_pdf = MagicMock(return_value=BytesIO(b"pdf data"))

        result = service.generate_attendance_report(mock_db, filters, "admin")

        assert isinstance(result, BytesIO)


class TestGenerateTestsReport:
    """Tests para generate_tests_report."""

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_generate_tests_report_csv(self, mock_env, mock_ctrl):
        """Genera reporte de tests en CSV."""
        from app.services.report_service import ReportService

        service = ReportService()
        service.statistic_controller = MagicMock()
        service.statistic_controller.get_test_performance.return_value = {
            "tests_by_type": [
                {
                    "test_type": "sprint",
                    "total_tests": 10,
                    "avg_score": 75.5,
                    "min_score": 60.0,
                    "max_score": 90.0,
                }
            ],
            "top_performers": [],
        }

        mock_db = MagicMock()
        filters = ReportFilter(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), format="csv"
        )

        service._generate_tabular_report = MagicMock(return_value=BytesIO(b"csv"))
        service._build_metadata = MagicMock()

        result = service.generate_tests_report(mock_db, filters, "admin")

        assert isinstance(result, BytesIO)

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_generate_tests_report_pdf(self, mock_env, mock_ctrl):
        """Genera reporte de tests en PDF."""
        from app.services.report_service import ReportService

        service = ReportService()
        service.statistic_controller = MagicMock()
        service.statistic_controller.get_test_performance.return_value = {
            "tests_by_type": [
                {
                    "test_type": "sprint",
                    "total_tests": 10,
                    "avg_score": 75.5,
                    "min_score": 60.0,
                    "max_score": 90.0,
                }
            ],
            "top_performers": [],
        }

        mock_db = MagicMock()
        filters = ReportFilter(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), format="pdf"
        )

        service._build_metadata = MagicMock()
        service._render_pdf = MagicMock(return_value=BytesIO(b"pdf"))

        result = service.generate_tests_report(mock_db, filters, "admin")

        assert isinstance(result, BytesIO)


class TestGenerateStatisticsReport:
    """Tests para generate_statistics_report."""

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_generate_statistics_report_xlsx(self, mock_env, mock_ctrl):
        """Genera reporte de estadísticas en Excel."""
        from app.services.report_service import ReportService

        service = ReportService()
        service.statistic_controller = MagicMock()
        service.statistic_controller.get_club_overview.return_value = {
            "total_athletes": 50,
            "active_athletes": 45,
            "total_tests_conducted": 100,
            "gender_distribution": {},
        }

        mock_db = MagicMock()
        filters = ReportFilter(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), format="xlsx"
        )

        service._build_metadata = MagicMock()
        service._generate_tabular_report = MagicMock(return_value=BytesIO(b"xlsx"))

        result = service.generate_statistics_report(mock_db, filters, "admin")

        assert isinstance(result, BytesIO)

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_generate_statistics_report_csv(self, mock_env, mock_ctrl):
        """Genera reporte de estadísticas en CSV."""
        from app.services.report_service import ReportService

        service = ReportService()
        service.statistic_controller = MagicMock()
        service.statistic_controller.get_club_overview.return_value = {
            "total_athletes": 50,
            "active_athletes": 45,
            "total_tests_conducted": 100,
            "gender_distribution": {},
        }

        mock_db = MagicMock()
        filters = ReportFilter(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), format="csv"
        )

        service._build_metadata = MagicMock()
        service._generate_tabular_report = MagicMock(return_value=BytesIO(b"csv"))

        result = service.generate_statistics_report(mock_db, filters, "admin")

        assert isinstance(result, BytesIO)


class TestPrivateMethods:
    """Tests para métodos privados."""

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_build_metadata_exists(self, mock_env, mock_ctrl):
        """Verifica que _build_metadata existe."""
        from app.services.report_service import ReportService

        service = ReportService()

        assert hasattr(service, "_build_metadata")
        assert callable(service._build_metadata)

    @patch("app.services.report_service.HTML")
    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_render_pdf_exists(self, mock_env, mock_ctrl, mock_html):
        """Verifica que _render_pdf existe."""
        from app.services.report_service import ReportService

        service = ReportService()

        assert hasattr(service, "_render_pdf")
        assert callable(service._render_pdf)

    @patch("app.services.report_service.StatisticController")
    @patch("app.services.report_service.Environment")
    def test_generate_tabular_report_exists(self, mock_env, mock_ctrl):
        """Verifica que _generate_tabular_report existe."""
        from app.services.report_service import ReportService

        service = ReportService()

        assert hasattr(service, "_generate_tabular_report")
        assert callable(service._generate_tabular_report)
