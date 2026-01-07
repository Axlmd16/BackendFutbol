"""DAO específico para estadísticas con métodos de consulta agregados."""

import logging
from datetime import date, datetime
from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.athlete import Athlete
from app.models.attendance import Attendance
from app.models.endurance_test import EnduranceTest
from app.models.evaluation import Evaluation
from app.models.sprint_test import SprintTest
from app.models.statistic import Statistic
from app.models.technical_assessment import TechnicalAssessment
from app.models.test import Test
from app.models.yoyo_test import YoyoTest
from app.utils.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class StatisticDAO(BaseDAO[Statistic]):
    """DAO específico para estadísticas de atletas."""

    def __init__(self):
        super().__init__(Statistic)

    def get_club_overview(
        self,
        db: Session,
        type_athlete: Optional[str] = None,
        sex: Optional[str] = None,
    ) -> dict:
        """
        Obtener métricas generales del club.

        Returns:
            Dict con totales y distribuciones
        """
        try:
            # Base query for athletes
            query = db.query(Athlete)

            if type_athlete:
                query = query.filter(Athlete.type_athlete == type_athlete)
            if sex:
                query = query.filter(Athlete.sex == sex)

            # Total athletes
            total = query.count()
            active = query.filter(Athlete.is_active.is_(True)).count()
            inactive = total - active

            # Distribution by type
            type_distribution = (
                db.query(
                    Athlete.type_athlete,
                    func.count(Athlete.id).label("count"),
                )
                .filter(Athlete.is_active.is_(True))
                .group_by(Athlete.type_athlete)
                .all()
            )

            athletes_by_type = []
            for row in type_distribution:
                pct = (row.count / active * 100) if active > 0 else 0
                athletes_by_type.append(
                    {
                        "type_athlete": row.type_athlete or "Sin tipo",
                        "count": row.count,
                        "percentage": round(pct, 1),
                    }
                )

            # Distribution by gender
            gender_distribution = (
                db.query(
                    Athlete.sex,
                    func.count(Athlete.id).label("count"),
                )
                .filter(Athlete.is_active.is_(True))
                .group_by(Athlete.sex)
                .all()
            )

            athletes_by_gender = []
            for row in gender_distribution:
                pct = (row.count / active * 100) if active > 0 else 0
                athletes_by_gender.append(
                    {
                        "sex": row.sex or "No especificado",
                        "count": row.count,
                        "percentage": round(pct, 1),
                    }
                )

            # Total evaluations
            eval_count = db.query(func.count(Evaluation.id)).scalar() or 0

            # Total tests (sum of all test types)
            total_tests = db.query(func.count(Test.id)).scalar() or 0

            return {
                "total_athletes": total,
                "active_athletes": active,
                "inactive_athletes": inactive,
                "athletes_by_type": athletes_by_type,
                "athletes_by_gender": athletes_by_gender,
                "total_evaluations": eval_count,
                "total_tests": total_tests,
            }

        except Exception as e:
            logger.error(f"Error getting club overview: {str(e)}")
            raise DatabaseException("Error al obtener resumen del club") from e

    def get_attendance_stats(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        type_athlete: Optional[str] = None,
        sex: Optional[str] = None,
        athlete_id: Optional[int] = None,
    ) -> dict:
        """
        Obtener estadísticas de asistencia con filtros.

        Returns:
            Dict con tasas y tendencias de asistencia
        """
        try:
            # Base query
            query = db.query(Attendance).filter(Attendance.is_active.is_(True))

            # Date filters
            if start_date:
                start_dt = datetime.combine(start_date, datetime.min.time())
                query = query.filter(Attendance.date >= start_dt)
            if end_date:
                end_dt = datetime.combine(end_date, datetime.max.time())
                query = query.filter(Attendance.date <= end_dt)

            # Join with athlete for type/sex/id filters
            if type_athlete or sex or athlete_id:
                query = query.join(Athlete, Attendance.athlete_id == Athlete.id)
                if type_athlete:
                    query = query.filter(Athlete.type_athlete == type_athlete)
                if sex:
                    query = query.filter(Athlete.sex == sex)
                if athlete_id:
                    query = query.filter(Athlete.id == athlete_id)

            # Total records
            total = query.count()
            present = query.filter(Attendance.is_present.is_(True)).count()
            absent = total - present
            rate = (present / total * 100) if total > 0 else 0

            # Attendance by date (for trend chart)
            date_stats = (
                db.query(
                    func.date(Attendance.date).label("att_date"),
                    func.count(Attendance.id).label("total"),
                    func.sum(case((Attendance.is_present.is_(True), 1), else_=0)).label(
                        "present"
                    ),
                )
                .filter(Attendance.is_active.is_(True))
                .group_by(func.date(Attendance.date))
                .order_by(func.date(Attendance.date).desc())
                .limit(30)
                .all()
            )

            attendance_by_period = []
            for row in date_stats:
                att_rate = (row.present / row.total * 100) if row.total > 0 else 0
                attendance_by_period.append(
                    {
                        "date": row.att_date.isoformat() if row.att_date else "",
                        "present_count": row.present or 0,
                        "absent_count": row.total - (row.present or 0),
                        "attendance_rate": round(att_rate, 1),
                    }
                )

            # Attendance by athlete type
            type_stats = (
                db.query(
                    Athlete.type_athlete,
                    func.count(Attendance.id).label("total"),
                    func.sum(case((Attendance.is_present.is_(True), 1), else_=0)).label(
                        "present"
                    ),
                )
                .join(Athlete, Attendance.athlete_id == Athlete.id)
                .filter(Attendance.is_active.is_(True))
                .group_by(Athlete.type_athlete)
                .all()
            )

            attendance_by_type = []
            for row in type_stats:
                att_rate = (row.present / row.total * 100) if row.total > 0 else 0
                attendance_by_type.append(
                    {
                        "type_athlete": row.type_athlete or "Sin tipo",
                        "total": row.total,
                        "present": row.present or 0,
                        "attendance_rate": round(att_rate, 1),
                    }
                )

            return {
                "total_records": total,
                "total_present": present,
                "total_absent": absent,
                "overall_attendance_rate": round(rate, 1),
                "attendance_by_period": attendance_by_period,
                "attendance_by_type": attendance_by_type,
            }

        except Exception as e:
            logger.error(f"Error getting attendance stats: {str(e)}")
            raise DatabaseException(
                "Error al obtener estadísticas de asistencia"
            ) from e

    def get_test_performance_stats(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        type_athlete: Optional[str] = None,
        athlete_id: Optional[int] = None,
    ) -> dict:
        """
        Obtener estadísticas de rendimiento en tests.

        Returns:
            Dict con totales por tipo y top performers
        """
        try:
            tests_by_type = []

            # Sprint tests
            sprint_query = db.query(
                func.count(SprintTest.id),
                func.avg(SprintTest.time_0_30_s),
                func.min(SprintTest.time_0_30_s),
                func.max(SprintTest.time_0_30_s),
            )
            if athlete_id:
                sprint_query = sprint_query.filter(SprintTest.athlete_id == athlete_id)

            sprint_stats = sprint_query.first()
            if sprint_stats and sprint_stats[0] > 0:
                # Formula: 4s = 100, 8s = 0
                avg_time = float(sprint_stats[1]) if sprint_stats[1] else 0
                score = (
                    max(0, min(100, 100 - ((avg_time - 4) * 25))) if avg_time > 0 else 0
                )

                tests_by_type.append(
                    {
                        "test_type": "Sprint Test",
                        "total_tests": sprint_stats[0],
                        "avg_score": round(score, 1),
                        "min_score": float(sprint_stats[2])
                        if sprint_stats[2]
                        else None,  # Raw time
                        "max_score": float(sprint_stats[3])
                        if sprint_stats[3]
                        else None,  # Raw time
                    }
                )

            # YoYo tests
            yoyo_query = db.query(
                func.count(YoyoTest.id),
                func.avg(YoyoTest.shuttle_count),
                func.min(YoyoTest.shuttle_count),
                func.max(YoyoTest.shuttle_count),
            )
            if athlete_id:
                yoyo_query = yoyo_query.filter(YoyoTest.athlete_id == athlete_id)
            yoyo_stats = yoyo_query.first()
            if yoyo_stats and yoyo_stats[0] > 0:
                # Formula: 20 shuttles = 30 pts
                avg_shuttles = float(yoyo_stats[1]) if yoyo_stats[1] else 0
                score = min(100, max(0, 30 + (avg_shuttles - 20) * 1.17))

                tests_by_type.append(
                    {
                        "test_type": "YoYo Test",
                        "total_tests": yoyo_stats[0],
                        "avg_score": round(score, 1),
                        "min_score": float(yoyo_stats[2]) if yoyo_stats[2] else None,
                        "max_score": float(yoyo_stats[3]) if yoyo_stats[3] else None,
                    }
                )

            # Endurance tests
            endurance_query = db.query(
                func.count(EnduranceTest.id),
                func.avg(EnduranceTest.total_distance_m),
                func.min(EnduranceTest.total_distance_m),
                func.max(EnduranceTest.total_distance_m),
            )
            if athlete_id:
                endurance_query = endurance_query.filter(
                    EnduranceTest.athlete_id == athlete_id
                )
            end_stats = endurance_query.first()
            if end_stats and end_stats[0] > 0:
                # Formula: 1000m = 30 pts
                avg_dist = float(end_stats[1]) if end_stats[1] else 0
                score = min(100, max(0, 30 + (avg_dist - 1000) * 0.035))

                tests_by_type.append(
                    {
                        "test_type": "Endurance Test",
                        "total_tests": end_stats[0],
                        "avg_score": round(score, 1),
                        "min_score": float(end_stats[2]) if end_stats[2] else None,
                        "max_score": float(end_stats[3]) if end_stats[3] else None,
                    }
                )

            # Technical assessments
            tech_query = db.query(func.count(TechnicalAssessment.id))
            if athlete_id:
                tech_query = tech_query.filter(
                    TechnicalAssessment.athlete_id == athlete_id
                )
            tech_count = tech_query.scalar() or 0
            if tech_count > 0:
                # Formula: 10 pts per test
                score = min(100, tech_count * 10)
                tests_by_type.append(
                    {
                        "test_type": "Technical Assessment",
                        "total_tests": tech_count,
                        "avg_score": score,
                        "min_score": None,
                        "max_score": None,
                    }
                )

            total_tests = sum(t["total_tests"] for t in tests_by_type)

            # Top performers (athletes with most tests completed)
            # Using Test model which has athlete_id
            top_query = (
                db.query(
                    Athlete.id,
                    Athlete.full_name,
                    Athlete.type_athlete,
                    func.count(Test.id).label("test_count"),
                )
                .join(Test, Test.athlete_id == Athlete.id)
                .filter(Athlete.is_active.is_(True))
            )
            if athlete_id:
                top_query = top_query.filter(Athlete.id == athlete_id)

            top_query = (
                top_query.group_by(Athlete.id, Athlete.full_name, Athlete.type_athlete)
                .order_by(func.count(Test.id).desc())
                .limit(5)
                .all()
            )

            top_performers = []
            for row in top_query:
                top_performers.append(
                    {
                        "athlete_id": row.id,
                        "athlete_name": row.full_name,
                        "athlete_type": row.type_athlete,
                        "avg_score": 0,  # Placeholder
                        "tests_completed": row.test_count,
                    }
                )

            return {
                "total_tests": total_tests,
                "tests_by_type": tests_by_type,
                "top_performers": top_performers,
            }

        except Exception as e:
            logger.error(f"Error getting test performance stats: {str(e)}")
            raise DatabaseException(
                "Error al obtener estadísticas de rendimiento"
            ) from e

    def get_athlete_individual_stats(self, db: Session, athlete_id: int) -> dict:
        """
        Obtener estadísticas individuales de un atleta específico.

        Returns:
            Dict con estadísticas físicas, de rendimiento, asistencia y tests
        """
        try:
            # Obtener atleta
            athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
            if not athlete:
                return None

            # Obtener estadísticas del atleta
            statistic = (
                db.query(Statistic).filter(Statistic.athlete_id == athlete_id).first()
            )

            # Estadísticas de asistencia
            attendance_query = db.query(
                func.count(Attendance.id).label("total"),
                func.sum(
                    case((Attendance.is_present == True, 1), else_=0)  # noqa: E712
                ).label("present"),
                func.sum(
                    case((Attendance.is_present == False, 1), else_=0)  # noqa: E712
                ).label("absent"),
            ).filter(Attendance.athlete_id == athlete_id)

            attendance_result = attendance_query.first()
            attendance_total = attendance_result.total or 0
            attendance_present = attendance_result.present or 0
            attendance_absent = attendance_result.absent or 0
            attendance_rate = (
                round((attendance_present / attendance_total) * 100, 1)
                if attendance_total > 0
                else 0.0
            )

            # Contar tests por tipo
            tests_by_type = []

            # Sprint tests
            sprint_count = (
                db.query(func.count(SprintTest.id))
                .filter(SprintTest.athlete_id == athlete_id)
                .filter(SprintTest.is_active.is_(True))
                .scalar()
                or 0
            )
            if sprint_count > 0:
                avg_time = (
                    db.query(func.avg(SprintTest.time_0_30_s))
                    .filter(SprintTest.athlete_id == athlete_id)
                    .filter(SprintTest.is_active.is_(True))
                    .scalar()
                )
                tests_by_type.append(
                    {
                        "test_type": "Sprint Test",
                        "count": sprint_count,
                        "avg_score": round(avg_time, 2) if avg_time else None,
                    }
                )

            # YoYo tests
            yoyo_count = (
                db.query(func.count(YoyoTest.id))
                .filter(YoyoTest.athlete_id == athlete_id)
                .filter(YoyoTest.is_active.is_(True))
                .scalar()
                or 0
            )
            if yoyo_count > 0:
                avg_shuttle = (
                    db.query(func.avg(YoyoTest.shuttle_count))
                    .filter(YoyoTest.athlete_id == athlete_id)
                    .filter(YoyoTest.is_active.is_(True))
                    .scalar()
                )
                tests_by_type.append(
                    {
                        "test_type": "YoYo Test",
                        "count": yoyo_count,
                        "avg_score": round(avg_shuttle, 1) if avg_shuttle else None,
                    }
                )

            # Endurance tests
            endurance_count = (
                db.query(func.count(EnduranceTest.id))
                .filter(EnduranceTest.athlete_id == athlete_id)
                .filter(EnduranceTest.is_active.is_(True))
                .scalar()
                or 0
            )
            if endurance_count > 0:
                avg_distance = (
                    db.query(func.avg(EnduranceTest.total_distance_m))
                    .filter(EnduranceTest.athlete_id == athlete_id)
                    .filter(EnduranceTest.is_active.is_(True))
                    .scalar()
                )
                tests_by_type.append(
                    {
                        "test_type": "Endurance Test",
                        "count": endurance_count,
                        "avg_score": round(avg_distance, 0) if avg_distance else None,
                    }
                )

            # Technical assessments
            tech_count = (
                db.query(func.count(TechnicalAssessment.id))
                .filter(TechnicalAssessment.athlete_id == athlete_id)
                .filter(TechnicalAssessment.is_active.is_(True))
                .scalar()
                or 0
            )
            if tech_count > 0:
                # Formula: 10 pts per test (same as controller)
                score = min(100, tech_count * 10)
                tests_by_type.append(
                    {
                        "test_type": "Technical Assessment",
                        "count": tech_count,
                        "avg_score": score,
                    }
                )

            tests_completed = sprint_count + yoyo_count + endurance_count + tech_count

            return {
                "athlete_id": athlete.id,
                "athlete_name": athlete.full_name,
                "type_athlete": athlete.type_athlete,
                "sex": athlete.sex.value if athlete.sex else "MALE",
                "is_active": athlete.is_active,
                # Estadísticas físicas
                "speed": statistic.speed if statistic else None,
                "stamina": statistic.stamina if statistic else None,
                "strength": statistic.strength if statistic else None,
                "agility": statistic.agility if statistic else None,
                # Estadísticas de rendimiento
                "matches_played": statistic.matches_played if statistic else 0,
                "goals": statistic.goals if statistic else 0,
                "assists": statistic.assists if statistic else 0,
                "yellow_cards": statistic.yellow_cards if statistic else 0,
                "red_cards": statistic.red_cards if statistic else 0,
                # Asistencia
                "attendance_total": attendance_total,
                "attendance_present": attendance_present,
                "attendance_absent": attendance_absent,
                "attendance_rate": attendance_rate,
                # Tests
                "tests_completed": tests_completed,
                "tests_by_type": tests_by_type,
            }

        except Exception as e:
            logger.error(f"Error getting individual athlete stats: {str(e)}")
            raise DatabaseException("Error al obtener estadísticas del atleta") from e

    # ================================================================
    # Métodos para cálculo de estadísticas desde tests
    # ================================================================

    def get_sprint_avg_time(self, db: Session, athlete_id: int) -> float | None:
        """Obtiene el promedio de tiempo 0-30m de SprintTests activos."""
        try:
            result = (
                db.query(func.avg(SprintTest.time_0_30_s))
                .filter(SprintTest.athlete_id == athlete_id)
                .filter(SprintTest.is_active == True)  # noqa: E712
                .scalar()
            )
            return float(result) if result is not None else None
        except Exception as e:
            logger.error(f"Error getting sprint avg: {e}")
            return None

    def get_yoyo_avg_shuttles(self, db: Session, athlete_id: int) -> float | None:
        """Obtiene el promedio de shuttle count de YoyoTests activos."""
        try:
            result = (
                db.query(func.avg(YoyoTest.shuttle_count))
                .filter(YoyoTest.athlete_id == athlete_id)
                .filter(YoyoTest.is_active == True)  # noqa: E712
                .scalar()
            )
            return float(result) if result is not None else None
        except Exception as e:
            logger.error(f"Error getting yoyo avg: {e}")
            return None

    def get_endurance_avg_distance(self, db: Session, athlete_id: int) -> float | None:
        """Obtiene el promedio de distancia de EnduranceTests activos."""
        try:
            result = (
                db.query(func.avg(EnduranceTest.total_distance_m))
                .filter(EnduranceTest.athlete_id == athlete_id)
                .filter(EnduranceTest.is_active == True)  # noqa: E712
                .scalar()
            )
            return float(result) if result is not None else None
        except Exception as e:
            logger.error(f"Error getting endurance avg: {e}")
            return None

    def get_technical_count(self, db: Session, athlete_id: int) -> int:
        """Obtiene la cantidad de TechnicalAssessments activos."""
        try:
            result = (
                db.query(func.count(TechnicalAssessment.id))
                .filter(TechnicalAssessment.athlete_id == athlete_id)
                .filter(TechnicalAssessment.is_active == True)  # noqa: E712
                .scalar()
            )
            return int(result) if result else 0
        except Exception as e:
            logger.error(f"Error getting technical count: {e}")
            return 0

    def get_athlete_statistic(self, db: Session, athlete_id: int) -> Statistic | None:
        """Obtiene el registro Statistic de un atleta."""
        try:
            return (
                db.query(Statistic).filter(Statistic.athlete_id == athlete_id).first()
            )
        except Exception as e:
            logger.error(f"Error getting athlete statistic: {e}")
            return None

    def update_statistic_fields(
        self, db: Session, statistic: Statistic, fields: dict
    ) -> Statistic:
        """Actualiza los campos de un registro Statistic."""
        try:
            for key, value in fields.items():
                if hasattr(statistic, key):
                    setattr(statistic, key, value)
            db.commit()
            db.refresh(statistic)
            return statistic
        except Exception as e:
            logger.error(f"Error updating statistic: {e}")
            db.rollback()
            raise DatabaseException("Error al actualizar estadísticas") from e
