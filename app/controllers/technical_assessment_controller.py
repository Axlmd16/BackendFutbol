from datetime import datetime

from sqlalchemy.orm import Session

from app.dao.athlete_dao import AthleteDAO
from app.dao.evaluation_dao import EvaluationDAO
from app.dao.technical_assessment_dao import TechnicalAssessmentDAO
from app.dao.test_dao import TestDAO
from app.models.test import Test
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
        evaluation_id: int,
        athlete_id: int,
        date: datetime,
        ball_control: str | None = None,
        short_pass: str | None = None,
        long_pass: str | None = None,
        shooting: str | None = None,
        dribbling: str | None = None,
        observations: str | None = None,
    ) -> Test:
        """Crear TechnicalAssessment para una evaluación y atleta dados."""
        if not self.evaluation_dao.get_by_id(db, evaluation_id):
            raise DatabaseException(f"Evaluación {evaluation_id} no existe")
        if not self.athlete_dao.get_by_id(db, athlete_id):
            raise DatabaseException(f"Atleta {athlete_id} no existe")

        return self.test_dao.create_technical_assessment(
            db=db,
            date=date,
            athlete_id=athlete_id,
            evaluation_id=evaluation_id,
            ball_control=ball_control,
            short_pass=short_pass,
            long_pass=long_pass,
            shooting=shooting,
            dribbling=dribbling,
            observations=observations,
        )

    def update_test(self, db: Session, test_id: int, **fields) -> Test | None:
        """Actualizar un TechnicalAssessment existente."""
        if "evaluation_id" in fields and fields["evaluation_id"] is not None:
            if not self.evaluation_dao.get_by_id(db, fields["evaluation_id"]):
                raise DatabaseException(
                    f"Evaluación {fields['evaluation_id']} no existe"
                )

        if "athlete_id" in fields and fields["athlete_id"] is not None:
            if not self.athlete_dao.get_by_id(db, fields["athlete_id"]):
                raise DatabaseException(f"Atleta {fields['athlete_id']} no existe")

        existing = self.technical_assessment_dao.get_by_id(
            db, test_id, only_active=True
        )
        if not existing:
            return None

        if not fields:
            return existing

        return self.technical_assessment_dao.update(db, test_id, fields)
