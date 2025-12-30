from datetime import datetime

from sqlalchemy.orm import Session

from app.dao.athlete_dao import AthleteDAO
from app.dao.evaluation_dao import EvaluationDAO
from app.dao.sprint_test_dao import SprintTestDAO
from app.dao.test_dao import TestDAO
from app.models.test import Test
from app.utils.exceptions import DatabaseException


class SprintTestController:
    """Controlador de pruebas de sprint."""

    def __init__(self):
        self.sprint_test_dao = SprintTestDAO()
        self.test_dao = TestDAO()
        self.evaluation_dao = EvaluationDAO()
        self.athlete_dao = AthleteDAO()

    def add_test(
        self,
        db: Session,
        evaluation_id: int,
        athlete_id: int,
        date: datetime,
        distance_meters: float,
        time_0_10_s: float,
        time_0_30_s: float,
        observations: str | None = None,
    ) -> Test:
        """Crear SprintTest para una evaluación y atleta dados."""
        if not self.evaluation_dao.get_by_id(db, evaluation_id):
            raise DatabaseException(f"Evaluación {evaluation_id} no existe")
        if not self.athlete_dao.get_by_id(db, athlete_id):
            raise DatabaseException(f"Atleta {athlete_id} no existe")

        return self.test_dao.create_sprint_test(
            db=db,
            date=date,
            athlete_id=athlete_id,
            evaluation_id=evaluation_id,
            distance_meters=distance_meters,
            time_0_10_s=time_0_10_s,
            time_0_30_s=time_0_30_s,
            observations=observations,
        )
