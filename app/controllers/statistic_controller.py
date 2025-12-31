"""Controlador de estadísticas con lógica de negocio."""

import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.dao.statistic_dao import StatisticDAO
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)


class StatisticController:
    """Controlador de estadísticas de atletas."""

    def __init__(self):
        self.statistic_dao = StatisticDAO()

    def get_club_overview(
        self,
        db: Session,
        type_athlete: Optional[str] = None,
        sex: Optional[str] = None,
    ) -> dict:
        """
        Obtener métricas generales del club.

        Args:
            db: Sesión de base de datos
            type_athlete: Filtro por tipo de atleta
            sex: Filtro por sexo

        Returns:
            Dict con métricas del club
        """
        try:
            return self.statistic_dao.get_club_overview(
                db=db,
                type_athlete=type_athlete,
                sex=sex,
            )
        except Exception as e:
            logger.error(f"Error getting club overview: {str(e)}")
            raise AppException(f"Error al obtener resumen del club: {str(e)}") from e

    def get_attendance_statistics(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        type_athlete: Optional[str] = None,
        sex: Optional[str] = None,
    ) -> dict:
        """
        Obtener estadísticas de asistencia.

        Args:
            db: Sesión de base de datos
            start_date: Fecha de inicio
            end_date: Fecha de fin
            type_athlete: Filtro por tipo de atleta
            sex: Filtro por sexo

        Returns:
            Dict con estadísticas de asistencia
        """
        try:
            return self.statistic_dao.get_attendance_stats(
                db=db,
                start_date=start_date,
                end_date=end_date,
                type_athlete=type_athlete,
                sex=sex,
            )
        except Exception as e:
            logger.error(f"Error getting attendance statistics: {str(e)}")
            raise AppException(
                f"Error al obtener estadísticas de asistencia: {str(e)}"
            ) from e

    def get_test_performance(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        type_athlete: Optional[str] = None,
    ) -> dict:
        """
        Obtener estadísticas de rendimiento en tests.

        Args:
            db: Sesión de base de datos
            start_date: Fecha de inicio
            end_date: Fecha de fin
            type_athlete: Filtro por tipo de atleta

        Returns:
            Dict con estadísticas de tests
        """
        try:
            return self.statistic_dao.get_test_performance_stats(
                db=db,
                start_date=start_date,
                end_date=end_date,
                type_athlete=type_athlete,
            )
        except Exception as e:
            logger.error(f"Error getting test performance: {str(e)}")
            raise AppException(
                f"Error al obtener rendimiento de tests: {str(e)}"
            ) from e
