from datetime import datetime

from sqlalchemy.orm import Session

from app.dao.athlete_dao import AthleteDAO
from app.dao.endurance_test_dao import EnduranceTestDAO
from app.dao.evaluation_dao import EvaluationDAO
from app.dao.test_dao import TestDAO
from app.models.test import Test
from app.utils.exceptions import DatabaseException


class EnduranceTestController:
    """Controlador de pruebas de resistencia."""

    def __init__(self):
        self.endurance_test_dao = EnduranceTestDAO()
        self.test_dao = TestDAO()
        self.evaluation_dao = EvaluationDAO()
        self.athlete_dao = AthleteDAO()

    def add_test(
        self,
        db: Session,
        evaluation_id: int,
        athlete_id: int,
        date: datetime,
        min_duration: int,
        total_distance_m: float,
        observations: str | None = None,
    ) -> Test:
        """Crear EnduranceTest para una evaluación y atleta dados."""
        if not self.evaluation_dao.get_by_id(db, evaluation_id):
            raise DatabaseException(f"Evaluación {evaluation_id} no existe")
        if not self.athlete_dao.get_by_id(db, athlete_id):
            raise DatabaseException(f"Atleta {athlete_id} no existe")

        return self.test_dao.create_endurance_test(
            db=db,
            date=date,
            athlete_id=athlete_id,
            evaluation_id=evaluation_id,
            min_duration=min_duration,
            total_distance_m=total_distance_m,
            observations=observations,
        )
