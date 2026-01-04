from datetime import datetime

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.controllers.statistic_controller import statistic_controller
from app.dao.athlete_dao import AthleteDAO
from app.dao.evaluation_dao import EvaluationDAO
from app.dao.test_dao import TestDAO
from app.dao.yoyo_test_dao import YoyoTestDAO
from app.models.test import Test
from app.models.yoyo_test import YoyoTest
from app.schemas.yoyo_test_schema import YoyoTestFilter
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

        test = self.test_dao.create_yoyo_test(
            db=db,
            date=date,
            athlete_id=athlete_id,
            evaluation_id=evaluation_id,
            shuttle_count=shuttle_count,
            final_level=final_level,
            failures=failures,
            observations=observations,
        )

        # Actualizar estadísticas del atleta
        statistic_controller.update_athlete_stats(db, athlete_id)

        return test

    def update_test(self, db: Session, test_id: int, **fields) -> Test | None:
        """Actualizar un YoyoTest existente."""
        if "evaluation_id" in fields and fields["evaluation_id"] is not None:
            if not self.evaluation_dao.get_by_id(db, fields["evaluation_id"]):
                raise DatabaseException(
                    f"Evaluación {fields['evaluation_id']} no existe"
                )

        if "athlete_id" in fields and fields["athlete_id"] is not None:
            if not self.athlete_dao.get_by_id(db, fields["athlete_id"]):
                raise DatabaseException(f"Atleta {fields['athlete_id']} no existe")

        existing = self.yoyo_test_dao.get_by_id(db, test_id, only_active=True)
        if not existing:
            return None

        if not fields:
            return existing

        return self.yoyo_test_dao.update(db, test_id, fields)

    def delete_test(self, db: Session, test_id: int) -> bool:
        """Eliminar un YoyoTest existente."""
        existing = self.yoyo_test_dao.get_by_id(db, test_id, only_active=True)
        if not existing:
            return False

        self.yoyo_test_dao.delete(db, test_id)

        # Actualizar estadísticas del atleta
        statistic_controller.update_athlete_stats(db, existing.athlete_id)

        return True

    def list_tests(
        self, db: Session, filters: YoyoTestFilter
    ) -> tuple[list[YoyoTest], int]:
        """Listar Yoyo Tests con paginación y filtros básicos."""
        query = db.query(YoyoTest).filter(YoyoTest.is_active)

        if filters.evaluation_id:
            query = query.filter(YoyoTest.evaluation_id == filters.evaluation_id)
        if filters.athlete_id:
            query = query.filter(YoyoTest.athlete_id == filters.athlete_id)

        total = query.with_entities(func.count()).scalar() or 0

        items = (
            query.order_by(desc(YoyoTest.date))
            .offset(filters.skip)
            .limit(filters.limit)
            .all()
        )

        return items, total
