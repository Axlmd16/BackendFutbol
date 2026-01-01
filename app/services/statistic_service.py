"""
Service para actualizar estadísticas de atletas basado en resultados de tests.

Este servicio mantiene la lógica de actualización de estadísticas separada
de los controladores de tests.
"""

import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.athlete import Athlete
from app.models.endurance_test import EnduranceTest
from app.models.sprint_test import SprintTest
from app.models.statistic import Statistic
from app.models.technical_assessment import TechnicalAssessment
from app.models.yoyo_test import YoyoTest

logger = logging.getLogger(__name__)


class StatisticService:
    """
    Servicio para recalcular y actualizar estadísticas de atletas.

    Mapeo de tests a estadísticas:
    - SprintTest → speed (basado en tiempo, menor = más rápido)
    - YoyoTest → stamina (resistencia aeróbica)
    - EnduranceTest → stamina (resistencia)
    - TechnicalAssessment → agility (habilidades técnicas)
    """

    def update_athlete_stats(self, db: Session, athlete_id: int) -> Optional[Statistic]:
        """
        Recalcula y actualiza las estadísticas físicas de un atleta
        basándose en todos sus tests completados.

        Args:
            db: Sesión de base de datos
            athlete_id: ID del atleta

        Returns:
            Statistic actualizado o None si no existe el atleta
        """
        try:
            # Verificar que el atleta existe
            athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
            if not athlete:
                logger.warning(f"Atleta {athlete_id} no encontrado")
                return None

            # Obtener o crear estadísticas
            statistic = (
                db.query(Statistic).filter(Statistic.athlete_id == athlete_id).first()
            )

            if not statistic:
                logger.warning(f"Statistic no encontrado para atleta {athlete_id}")
                return None

            # Calcular velocidad desde SprintTests
            speed = self._calculate_speed(db, athlete_id)
            if speed is not None:
                statistic.speed = speed

            # Calcular stamina desde YoyoTests y EnduranceTests
            stamina = self._calculate_stamina(db, athlete_id)
            if stamina is not None:
                statistic.stamina = stamina

            # Calcular agilidad desde TechnicalAssessments
            agility = self._calculate_agility(db, athlete_id)
            if agility is not None:
                statistic.agility = agility

            db.commit()
            db.refresh(statistic)

            logger.info(
                f"Estadísticas actualizadas para atleta {athlete_id}: "
                f"speed={statistic.speed}, stamina={statistic.stamina}, "
                f"agility={statistic.agility}"
            )

            return statistic

        except Exception as e:
            logger.error(
                f"Error actualizando estadísticas para atleta {athlete_id}: {e}"
            )
            db.rollback()
            raise

    def _calculate_speed(self, db: Session, athlete_id: int) -> Optional[float]:
        """
        Calcula velocidad promedio desde SprintTests.
        Basado en tiempo de 30m - menor tiempo = mayor velocidad.
        Convierte a escala 0-100 donde 100 es lo mejor.
        """
        result = (
            db.query(func.avg(SprintTest.time_0_30_s))
            .filter(SprintTest.athlete_id == athlete_id)
            .filter(SprintTest.is_active == True)  # noqa: E712
            .scalar()
        )

        if result is None:
            return None

        # Conversión: tiempo promedio a puntuación de velocidad
        # Asumiendo que 4s = excelente (100) y 8s = malo (0)
        # Formula: speed = 100 - ((tiempo - 4) * 25)
        avg_time = float(result)
        speed_score = max(0, min(100, 100 - ((avg_time - 4) * 25)))
        return round(speed_score, 1)

    def _calculate_stamina(self, db: Session, athlete_id: int) -> Optional[float]:
        """
        Calcula resistencia desde YoyoTests y EnduranceTests.
        Combina shuttle count y distancia recorrida.
        """
        # YoYo: shuttle count (más = mejor)
        yoyo_avg = (
            db.query(func.avg(YoyoTest.shuttle_count))
            .filter(YoyoTest.athlete_id == athlete_id)
            .filter(YoyoTest.is_active == True)  # noqa: E712
            .scalar()
        )

        # Endurance: distancia en metros (más = mejor)
        endurance_avg = (
            db.query(func.avg(EnduranceTest.total_distance_m))
            .filter(EnduranceTest.athlete_id == athlete_id)
            .filter(EnduranceTest.is_active == True)  # noqa: E712
            .scalar()
        )

        scores = []

        if yoyo_avg is not None:
            # Shuttle count: 20 = bajo (30), 80 = alto (100)
            yoyo_score = min(100, max(0, 30 + (float(yoyo_avg) - 20) * 1.17))
            scores.append(yoyo_score)

        if endurance_avg is not None:
            # Distancia: 1000m = bajo (30), 3000m = alto (100)
            endurance_score = min(
                100, max(0, 30 + (float(endurance_avg) - 1000) * 0.035)
            )
            scores.append(endurance_score)

        if not scores:
            return None

        return round(sum(scores) / len(scores), 1)

    def _calculate_agility(self, db: Session, athlete_id: int) -> Optional[float]:
        """
        Calcula agilidad desde TechnicalAssessments.
        Promedia las habilidades técnicas evaluadas.
        """
        # Contar assessments completados como proxy de nivel técnico
        count = (
            db.query(func.count(TechnicalAssessment.id))
            .filter(TechnicalAssessment.athlete_id == athlete_id)
            .filter(TechnicalAssessment.is_active == True)  # noqa: E712
            .scalar()
        )

        if not count or count == 0:
            return None

        # Por ahora, usar número de evaluaciones como proxy
        # Cada evaluación completada suma 10 puntos (hasta 100)
        agility_score = min(100, count * 10)
        return float(agility_score)


# Singleton para uso en controladores
statistic_service = StatisticService()
