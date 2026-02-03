"""Controlador de estadísticas con lógica de negocio."""

import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.dao.statistic_dao import StatisticDAO
from app.schemas.statistic_schema import UpdateSportsStatsRequest
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
        athlete_id: Optional[int] = None,
    ) -> dict:
        """
        Obtener estadísticas de asistencia.

        Args:
            db: Sesión de base de datos
            start_date: Fecha de inicio
            end_date: Fecha de fin
            type_athlete: Filtro por tipo de atleta
            sex: Filtro por sexo
            athlete_id: Filtro por atleta específico

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
                athlete_id=athlete_id,
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
        athlete_id: Optional[int] = None,
    ) -> dict:
        """
        Obtener estadísticas de rendimiento en tests.

        Args:
            db: Sesión de base de datos
            start_date: Fecha de inicio
            end_date: Fecha de fin
            type_athlete: Filtro por tipo de atleta
            athlete_id: Filtro por atleta específico

        Returns:
            Dict con estadísticas de tests
        """
        try:
            return self.statistic_dao.get_test_performance_stats(
                db=db,
                start_date=start_date,
                end_date=end_date,
                type_athlete=type_athlete,
                athlete_id=athlete_id,
            )
        except Exception as e:
            logger.error(f"Error getting test performance: {str(e)}")
            raise AppException(
                f"Error al obtener rendimiento de tests: {str(e)}"
            ) from e

    def get_athlete_individual_stats(self, db: Session, athlete_id: int) -> dict:
        """
        Obtener estadísticas individuales de un atleta.

        Args:
            db: Sesión de base de datos
            athlete_id: ID del atleta

        Returns:
            Dict con estadísticas individuales del atleta o None si no existe
        """
        try:
            result = self.statistic_dao.get_athlete_individual_stats(
                db=db,
                athlete_id=athlete_id,
            )
            if result is None:
                return None
            return result
        except Exception as e:
            logger.error(f"Error getting athlete individual stats: {str(e)}")
            raise AppException(
                f"Error al obtener estadísticas del atleta: {str(e)}"
            ) from e

    def update_athlete_stats(self, db: Session, athlete_id: int) -> dict | None:
        """
        Recalcula y actualiza las estadísticas físicas de un atleta
        basándose en sus tests completados.

        Lógica de negocio:
        - speed: Basado en tiempo promedio de SprintTests (4s=100, 8s=0)
        - stamina: Combinación de YoyoTests y EnduranceTests
        - agility: Basado en cantidad de TechnicalAssessments

        Args:
            db: Sesión de base de datos
            athlete_id: ID del atleta

        Returns:
            Dict con estadísticas actualizadas o None si no existe
        """
        try:
            # Obtener el registro Statistic del atleta
            statistic = self.statistic_dao.get_athlete_statistic(db, athlete_id)
            print(f"[DEBUG] Statistic encontrado: {statistic}")
            if not statistic:
                logger.warning(f"Statistic no encontrado para atleta {athlete_id}")
                return None

            updates = {}

            # VELOCIDAD (SprintTest)
            sprint_avg = self.statistic_dao.get_sprint_avg_time(db, athlete_id)
            print(f"[DEBUG] Sprint avg time: {sprint_avg}")
            if sprint_avg is not None:
                # Fórmula: 4 segundos = 100 (excelente), 8 segundos = 0 (malo)
                speed_score = max(0, min(100, 100 - ((sprint_avg - 4) * 25)))
                updates["speed"] = round(speed_score, 1)
                print(f"[DEBUG] Speed score calculado: {speed_score}")
            else:
                updates["speed"] = None

            # RESISTENCIA (YoyoTest + EnduranceTest)
            yoyo_avg = self.statistic_dao.get_yoyo_avg_shuttles(db, athlete_id)
            endurance_avg = self.statistic_dao.get_endurance_avg_distance(
                db, athlete_id
            )
            stamina_scores = []

            if yoyo_avg is not None:
                # Shuttle count: 20 = 30 puntos, 80 = 100 puntos
                yoyo_score = min(100, max(0, 30 + (yoyo_avg - 20) * 1.17))
                stamina_scores.append(yoyo_score)

            if endurance_avg is not None:
                # Distancia: 1000m = 30 puntos, 3000m = 100 puntos
                endurance_score = min(100, max(0, 30 + (endurance_avg - 1000) * 0.035))
                stamina_scores.append(endurance_score)

            if stamina_scores:
                updates["stamina"] = round(sum(stamina_scores) / len(stamina_scores), 1)
            else:
                updates["stamina"] = None

            # AGILIDAD (TechnicalAssessment)
            tech_count = self.statistic_dao.get_technical_count(db, athlete_id)
            if tech_count > 0:
                # Cada evaluación técnica suma 10 puntos (máximo 100)
                updates["agility"] = min(100, tech_count * 10)
            else:
                updates["agility"] = None

            # Actualizar en la base de datos
            if updates:
                self.statistic_dao.update_statistic_fields(db, statistic, updates)
                logger.info(f"Stats actualizadas para atleta {athlete_id}: {updates}")

            return updates

        except Exception as e:
            logger.error(f"Error updating athlete stats: {str(e)}")
            raise AppException(
                f"Error al actualizar estadísticas del atleta: {str(e)}"
            ) from e

    def update_sports_stats(
        self, db: Session, athlete_id: int, payload: UpdateSportsStatsRequest
    ) -> dict | None:
        """
        Actualiza las estadísticas deportivas de un atleta.

        Args:
            db: Sesión de base de datos
            athlete_id: ID del atleta
            payload: Schema con campos a actualizar (matches_played, goals, etc.)

        Returns:
            Dict con estadísticas actualizadas o None si no existe
        """
        try:
            statistic = self.statistic_dao.get_athlete_statistic(db, athlete_id)
            if not statistic:
                logger.warning(f"Statistic no encontrado para atleta {athlete_id}")
                return None

            # Filtrar solo los campos no-None del request
            valid_fields = {
                "matches_played",
                "goals",
                "assists",
                "yellow_cards",
                "red_cards",
            }
            filtered_updates = {
                k: v
                for k, v in payload.model_dump(exclude_none=True).items()
                if k in valid_fields
            }

            if filtered_updates:
                self.statistic_dao.update_statistic_fields(
                    db, statistic, filtered_updates
                )
                logger.info(
                    f"Stats deportivas actualizadas para atleta {athlete_id}: "
                    f"{filtered_updates}"
                )

            return {
                "athlete_id": athlete_id,
                "matches_played": statistic.matches_played,
                "goals": statistic.goals,
                "assists": statistic.assists,
                "yellow_cards": statistic.yellow_cards,
                "red_cards": statistic.red_cards,
            }

        except Exception as e:
            logger.error(f"Error updating sports stats: {str(e)}")
            raise AppException(
                f"Error al actualizar estadísticas deportivas: {str(e)}"
            ) from e


# Singleton para uso en otros controladores
statistic_controller = StatisticController()
