from typing import List

from sqlalchemy.orm import Session

from app.dao.evaluation_dao import EvaluationDAO
from app.dao.test_dao import TestDAO
from app.models.test import Test
from app.utils.exceptions import DatabaseException


class TestController:
    """Controlador de pruebas base."""

    __test__ = False  # evitar que pytest lo tome como test

    def __init__(self):
        self.test_dao = TestDAO()
        self.evaluation_dao = EvaluationDAO()

    def list_tests_by_evaluation(self, db: Session, evaluation_id: int) -> List[Test]:
        if not self.evaluation_dao.get_by_id(db, evaluation_id):
            raise DatabaseException(f"Evaluación {evaluation_id} no existe")
        return self.test_dao.list_by_evaluation(db, evaluation_id)

    def delete_test(self, db: Session, test_id: int) -> bool:
        return self.test_dao.delete(db, test_id)
