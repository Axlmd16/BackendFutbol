"""Controlador de reportes deportivos - Refactorizado."""

import logging
from io import BytesIO

from sqlalchemy.orm import Session

from app.schemas.report_schema import ReportFilter, ReportType
from app.services.report_service import ReportService
from app.utils.exceptions import ValidationException

logger = logging.getLogger(__name__)


class ReportController:
    """Controlador de reportes que delega a ReportService."""

    def __init__(self):
        self.report_service = ReportService()

    def generate_report(
        self,
        db: Session,
        filters: ReportFilter,
        user_name: str,
    ) -> BytesIO:
        """
        Genera un reporte según el tipo especificado.

        Args:
            db: Sesión de BD
            filters: Filtros del reporte
            user_name: Usuario que genera el reporte

        Returns:
            BytesIO con el reporte generado

        Raises:
            ValidationException: Si el tipo de reporte no es válido
        """
        try:
            # Validar tipo de reporte
            if not filters.report_type:
                raise ValidationException(
                    "Debe especificar un tipo de reporte (attendance, tests, statistics"
                )

            # Delegar a ReportService según tipo
            if filters.report_type == ReportType.ATTENDANCE:
                return self.report_service.generate_attendance_report(
                    db=db, filters=filters, user_name=user_name
                )
            elif filters.report_type == ReportType.TESTS:
                return self.report_service.generate_tests_report(
                    db=db, filters=filters, user_name=user_name
                )
            elif filters.report_type == ReportType.STATISTICS:
                return self.report_service.generate_statistics_report(
                    db=db, filters=filters, user_name=user_name
                )
            else:
                raise ValidationException(
                    f"Tipo de reporte no válido: {filters.report_type}"
                )

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}")
            raise ValidationException(f"Error al generar reporte: {str(e)}") from e
