"""DAO para generación de reportes deportivos."""

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.athlete import Athlete
from app.models.evaluation import Evaluation
from app.models.endurance_test import EnduranceTest
from app.models.sprint_test import SprintTest
from app.models.technical_assessment import TechnicalAssessment
from app.models.yoyo_test import YoyoTest


class ReportDAO:
    """DAO para consultas de reportes."""

    def get_athletes_for_report(
        self,
        db: Session,
        club_id: Optional[int] = None,
        athlete_id: Optional[int] = None,
    ) -> List[Athlete]:
        """
        Obtiene atletas para el reporte.

        Args:
            db: Sesión de BD
            club_id: ID del club (filtro)
            athlete_id: ID del atleta (filtro)

        Returns:
            Lista de atletas
        """
        query = db.query(Athlete).filter(Athlete.is_active == True)

        if club_id:
            query = query.filter(Athlete.club_id == club_id)

        if athlete_id:
            query = query.filter(Athlete.id == athlete_id)

        return query.order_by(Athlete.full_name).all()

    def get_attendance_records(
        self,
        db: Session,
        athlete_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Attendance]:
        """
        Obtiene registros de asistencia para atletas.

        Args:
            db: Sesión de BD
            athlete_ids: IDs de atletas
            start_date: Fecha inicio
            end_date: Fecha fin

        Returns:
            Lista de registros de asistencia
        """
        query = db.query(Attendance).filter(Attendance.athlete_id.in_(athlete_ids))

        if start_date:
            query = query.filter(Attendance.attendance_date >= start_date)

        if end_date:
            query = query.filter(Attendance.attendance_date <= end_date)

        return query.order_by(
            Attendance.athlete_id, Attendance.attendance_date.desc()
        ).all()

    def get_evaluations(
        self,
        db: Session,
        athlete_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Evaluation]:
        """
        Obtiene evaluaciones para atletas.

        Args:
            db: Sesión de BD
            athlete_ids: IDs de atletas
            start_date: Fecha inicio
            end_date: Fecha fin

        Returns:
            Lista de evaluaciones
        """
        query = db.query(Evaluation).filter(Evaluation.athlete_id.in_(athlete_ids))

        if start_date:
            query = query.filter(Evaluation.created_at >= start_date)

        if end_date:
            query = query.filter(Evaluation.created_at <= end_date)

        return query.order_by(
            Evaluation.athlete_id, Evaluation.created_at.desc()
        ).all()

    def get_sprint_tests(
        self,
        db: Session,
        athlete_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[SprintTest]:
        """
        Obtiene pruebas de velocidad (sprint) para atletas.

        Args:
            db: Sesión de BD
            athlete_ids: IDs de atletas
            start_date: Fecha inicio
            end_date: Fecha fin

        Returns:
            Lista de pruebas de sprint
        """
        query = db.query(SprintTest).filter(SprintTest.athlete_id.in_(athlete_ids))

        if start_date:
            query = query.filter(SprintTest.created_at >= start_date)

        if end_date:
            query = query.filter(SprintTest.created_at <= end_date)

        return query.order_by(
            SprintTest.athlete_id, SprintTest.created_at.desc()
        ).all()

    def get_endurance_tests(
        self,
        db: Session,
        athlete_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[EnduranceTest]:
        """
        Obtiene pruebas de resistencia para atletas.

        Args:
            db: Sesión de BD
            athlete_ids: IDs de atletas
            start_date: Fecha inicio
            end_date: Fecha fin

        Returns:
            Lista de pruebas de resistencia
        """
        query = db.query(EnduranceTest).filter(
            EnduranceTest.athlete_id.in_(athlete_ids)
        )

        if start_date:
            query = query.filter(EnduranceTest.created_at >= start_date)

        if end_date:
            query = query.filter(EnduranceTest.created_at <= end_date)

        return query.order_by(
            EnduranceTest.athlete_id, EnduranceTest.created_at.desc()
        ).all()

    def get_yoyo_tests(
        self,
        db: Session,
        athlete_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[YoyoTest]:
        """
        Obtiene pruebas Yo-Yo para atletas.

        Args:
            db: Sesión de BD
            athlete_ids: IDs de atletas
            start_date: Fecha inicio
            end_date: Fecha fin

        Returns:
            Lista de pruebas Yo-Yo
        """
        query = db.query(YoyoTest).filter(YoyoTest.athlete_id.in_(athlete_ids))

        if start_date:
            query = query.filter(YoyoTest.created_at >= start_date)

        if end_date:
            query = query.filter(YoyoTest.created_at <= end_date)

        return query.order_by(YoyoTest.athlete_id, YoyoTest.created_at.desc()).all()

    def get_technical_assessments(
        self,
        db: Session,
        athlete_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[TechnicalAssessment]:
        """
        Obtiene evaluaciones técnicas para atletas.

        Args:
            db: Sesión de BD
            athlete_ids: IDs de atletas
            start_date: Fecha inicio
            end_date: Fecha fin

        Returns:
            Lista de evaluaciones técnicas
        """
        query = db.query(TechnicalAssessment).filter(
            TechnicalAssessment.athlete_id.in_(athlete_ids)
        )

        if start_date:
            query = query.filter(TechnicalAssessment.created_at >= start_date)

        if end_date:
            query = query.filter(TechnicalAssessment.created_at <= end_date)

        return query.order_by(
            TechnicalAssessment.athlete_id, TechnicalAssessment.created_at.desc()
        ).all()

    def get_report_statistics(
        self,
        db: Session,
        athlete_ids: List[int],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Obtiene estadísticas para el resumen del reporte.

        Args:
            db: Sesión de BD
            athlete_ids: IDs de atletas
            start_date: Fecha inicio
            end_date: Fecha fin

        Returns:
            Diccionario con estadísticas
        """
        filters = [Attendance.athlete_id.in_(athlete_ids)] if athlete_ids else []
        if start_date:
            filters.append(Attendance.attendance_date >= start_date)
        if end_date:
            filters.append(Attendance.attendance_date <= end_date)

        attendance_count = db.query(func.count(Attendance.id))
        if filters:
            attendance_count = attendance_count.filter(and_(*filters))
        attendance_count = attendance_count.scalar() or 0

        eval_filters = [Evaluation.athlete_id.in_(athlete_ids)] if athlete_ids else []
        if start_date:
            eval_filters.append(Evaluation.created_at >= start_date)
        if end_date:
            eval_filters.append(Evaluation.created_at <= end_date)

        evaluations_count = db.query(func.count(Evaluation.id))
        if eval_filters:
            evaluations_count = evaluations_count.filter(and_(*eval_filters))
        evaluations_count = evaluations_count.scalar() or 0

        test_filters = [SprintTest.athlete_id.in_(athlete_ids)] if athlete_ids else []
        if start_date:
            test_filters.append(SprintTest.created_at >= start_date)
        if end_date:
            test_filters.append(SprintTest.created_at <= end_date)

        sprint_count = db.query(func.count(SprintTest.id))
        if test_filters:
            sprint_count = sprint_count.filter(and_(*test_filters))
        sprint_count = sprint_count.scalar() or 0

        return {
            "total_attendance": attendance_count,
            "total_evaluations": evaluations_count,
            "total_tests": sprint_count,
        }
