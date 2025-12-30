from datetime import datetime

from sqlalchemy.orm import Session

from app.dao.athlete_dao import AthleteDAO
from app.dao.evaluation_dao import EvaluationDAO
from app.dao.test_dao import TestDAO
from app.dao.yoyo_test_dao import YoyoTestDAO
from app.models.test import Test
from app.utils.exceptions import DatabaseException


class YoyoTestController:
    """Controlador de pruebas Yo-Yo."""

    def __init__(self):
        self.yoyo_test_dao = YoyoTestDAO()
        self.test_dao = TestDAO()
        self.evaluation_dao = EvaluationDAO()
        self.athlete_dao = AthleteDAO()

    def add_test(
        self,
        db: Session,
        evaluation_id: int,
        athlete_id: int,
        date: datetime,
        shuttle_count: int,
        final_level: str,
        failures: int,
        observations: str | None = None,
    ) -> Test:
        """Crear YoyoTest para una evaluación y atleta dados."""
        if not self.evaluation_dao.get_by_id(db, evaluation_id):
            raise DatabaseException(f"Evaluación {evaluation_id} no existe")
        if not self.athlete_dao.get_by_id(db, athlete_id):
            raise DatabaseException(f"Atleta {athlete_id} no existe")

        return self.test_dao.create_yoyo_test(
            db=db,
            date=date,
            athlete_id=athlete_id,
            evaluation_id=evaluation_id,
            shuttle_count=shuttle_count,
            final_level=final_level,
            failures=failures,
            observations=observations,
        )
