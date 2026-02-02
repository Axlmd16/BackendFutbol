from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.controllers.statistic_controller import statistic_controller
from app.dao.athlete_dao import AthleteDAO
from app.dao.evaluation_dao import EvaluationDAO
from app.dao.technical_assessment_dao import TechnicalAssessmentDAO
from app.dao.test_dao import TestDAO
from app.models.athlete import Athlete
from app.models.technical_assessment import TechnicalAssessment
from app.models.test import Test
from app.schemas.technical_assessment_schema import (
    CreateTechnicalAssessmentSchema,
    TechnicalAssessmentFilter,
    UpdateTechnicalAssessmentSchema,
)
from app.utils.exceptions import DatabaseException


class TechnicalAssessmentController:
    """Controlador de evaluaciones técnicas."""

    def __init__(self):
        self.technical_assessment_dao = TechnicalAssessmentDAO()
        self.test_dao = TestDAO()
        self.evaluation_dao = EvaluationDAO()
        self.athlete_dao = AthleteDAO()

    def add_test(
        self,
        db: Session,
        payload: CreateTechnicalAssessmentSchema,
    ) -> Test:
        """Crear TechnicalAssessment para una evaluación y atleta dados."""
        if not self.evaluation_dao.get_by_id(db, payload.evaluation_id):
            raise DatabaseException(f"Evaluación {payload.evaluation_id} no existe")
        if not self.athlete_dao.get_by_id(db, payload.athlete_id):
            raise DatabaseException(f"Atleta {payload.athlete_id} no existe")

        return self.test_dao.create_technical_assessment(
            db=db,
            date=payload.date,
            athlete_id=payload.athlete_id,
            evaluation_id=payload.evaluation_id,
            ball_control=payload.ball_control,
            short_pass=payload.short_pass,
            long_pass=payload.long_pass,
            shooting=payload.shooting,
            dribbling=payload.dribbling,
            observations=payload.observations,
        )

    def update_test(
        self,
        db: Session,
        test_id: int,
        payload: UpdateTechnicalAssessmentSchema,
    ) -> Test | None:
        """Actualizar un TechnicalAssessment existente."""
        fields = payload.model_dump(exclude_none=True)

        evaluation_id = fields.get("evaluation_id")
        if evaluation_id is not None and not self.evaluation_dao.get_by_id(
            db, evaluation_id
        ):
            raise DatabaseException(f"Evaluación {evaluation_id} no existe")

        athlete_id = fields.get("athlete_id")
        if athlete_id is not None and not self.athlete_dao.get_by_id(db, athlete_id):
            raise DatabaseException(f"Atleta {athlete_id} no existe")

        existing = self.technical_assessment_dao.get_by_id(
            db, test_id, only_active=True
        )
        if not existing:
            return None

        if not fields:
            return existing

        return self.technical_assessment_dao.update(db, test_id, fields)

    def delete_test(self, db: Session, test_id: int) -> bool:
        """Eliminar (desactivar) un TechnicalAssessment existente."""
        existing = self.technical_assessment_dao.get_by_id(
            db, test_id, only_active=True
        )
        if not existing:
            return False

        self.technical_assessment_dao.delete(db, test_id)

        # Actualizar estadísticas del atleta
        statistic_controller.update_athlete_stats(db, existing.athlete_id)

        return True

    def list_tests(
        self, db: Session, filters: TechnicalAssessmentFilter
    ) -> tuple[list[TechnicalAssessment], int]:
        """Listar Technical Assessments con paginación y filtros básicos."""
        query = db.query(TechnicalAssessment).filter(TechnicalAssessment.is_active)

        if filters.evaluation_id:
            query = query.filter(
                TechnicalAssessment.evaluation_id == filters.evaluation_id
            )
        if filters.athlete_id:
            query = query.filter(TechnicalAssessment.athlete_id == filters.athlete_id)
        if filters.search:
            query = query.join(Athlete).filter(
                Athlete.full_name.ilike(f"%{filters.search}%")
            )

        total = query.with_entities(func.count()).scalar() or 0

        items = (
            query.order_by(desc(TechnicalAssessment.date))
            .offset(filters.skip)
            .limit(filters.limit)
            .all()
        )

        return items, total
