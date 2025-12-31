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

            # Join with athlete for type/sex filters
            if type_athlete or sex:
                query = query.join(Athlete, Attendance.athlete_id == Athlete.id)
                if type_athlete:
                    query = query.filter(Athlete.type_athlete == type_athlete)
                if sex:
                    query = query.filter(Athlete.sex == sex)

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
    ) -> dict:
        """
        Obtener estadísticas de rendimiento en tests.

        Returns:
            Dict con totales por tipo y top performers
        """
        try:
            tests_by_type = []

            # Sprint tests
            sprint_count = db.query(func.count(SprintTest.id)).scalar() or 0
            if sprint_count > 0:
                tests_by_type.append(
                    {
                        "test_type": "Sprint Test",
                        "total_tests": sprint_count,
                        "avg_score": None,
                        "min_score": None,
                        "max_score": None,
                    }
                )

            # YoYo tests - using shuttle_count as numeric metric
            yoyo_query = db.query(
                func.count(YoyoTest.id),
                func.avg(YoyoTest.shuttle_count),
                func.min(YoyoTest.shuttle_count),
                func.max(YoyoTest.shuttle_count),
            )
            yoyo_stats = yoyo_query.first()
            if yoyo_stats and yoyo_stats[0] > 0:
                tests_by_type.append(
                    {
                        "test_type": "YoYo Test",
                        "total_tests": yoyo_stats[0],
                        "avg_score": round(float(yoyo_stats[1]), 2)
                        if yoyo_stats[1]
                        else None,
                        "min_score": float(yoyo_stats[2]) if yoyo_stats[2] else None,
                        "max_score": float(yoyo_stats[3]) if yoyo_stats[3] else None,
                    }
                )

            # Endurance tests - using total_distance_m
            endurance_query = db.query(
                func.count(EnduranceTest.id),
                func.avg(EnduranceTest.total_distance_m),
                func.min(EnduranceTest.total_distance_m),
                func.max(EnduranceTest.total_distance_m),
            )
            end_stats = endurance_query.first()
            if end_stats and end_stats[0] > 0:
                tests_by_type.append(
                    {
                        "test_type": "Endurance Test",
                        "total_tests": end_stats[0],
                        "avg_score": round(float(end_stats[1]), 2)
                        if end_stats[1]
                        else None,
                        "min_score": float(end_stats[2]) if end_stats[2] else None,
                        "max_score": float(end_stats[3]) if end_stats[3] else None,
                    }
                )

            # Technical assessments - no numeric score, just count
            tech_count = db.query(func.count(TechnicalAssessment.id)).scalar() or 0
            if tech_count > 0:
                tests_by_type.append(
                    {
                        "test_type": "Technical Assessment",
                        "total_tests": tech_count,
                        "avg_score": None,
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
                .group_by(Athlete.id, Athlete.full_name, Athlete.type_athlete)
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
