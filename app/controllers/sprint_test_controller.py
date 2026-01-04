from datetime import datetime

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.controllers.statistic_controller import statistic_controller
from app.dao.athlete_dao import AthleteDAO
from app.dao.evaluation_dao import EvaluationDAO
from app.dao.sprint_test_dao import SprintTestDAO
from app.dao.test_dao import TestDAO
from app.models.sprint_test import SprintTest
from app.models.test import Test
from app.schemas.sprint_test_schema import SprintTestFilter
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

        test = self.test_dao.create_sprint_test(
            db=db,
            date=date,
            athlete_id=athlete_id,
            evaluation_id=evaluation_id,
            distance_meters=distance_meters,
            time_0_10_s=time_0_10_s,
            time_0_30_s=time_0_30_s,
            observations=observations,
        )

        # Actualizar estadísticas del atleta
        print(
            f"[DEBUG] SprintTest creado. Llamando update_stats para atleta {athlete_id}"
        )
        result = statistic_controller.update_athlete_stats(db, athlete_id)
        print(f"[DEBUG] Resultado de update_athlete_stats: {result}")

        return test

    def update_test(self, db: Session, test_id: int, **fields) -> Test | None:
        """Actualizar un SprintTest existente."""
        if "evaluation_id" in fields and fields["evaluation_id"] is not None:
            if not self.evaluation_dao.get_by_id(db, fields["evaluation_id"]):
                raise DatabaseException(
                    f"Evaluación {fields['evaluation_id']} no existe"
                )

        if "athlete_id" in fields and fields["athlete_id"] is not None:
            if not self.athlete_dao.get_by_id(db, fields["athlete_id"]):
                raise DatabaseException(f"Atleta {fields['athlete_id']} no existe")

        existing = self.sprint_test_dao.get_by_id(db, test_id, only_active=True)
        if not existing:
            return None

        if not fields:
            return existing

        return self.sprint_test_dao.update(db, test_id, fields)

    def delete_test(self, db: Session, test_id: int) -> bool:
        """Eliminar un SprintTest existente."""
        existing = self.sprint_test_dao.get_by_id(db, test_id, only_active=True)
        if not existing:
            return False

        self.sprint_test_dao.delete(db, test_id)

        # Actualizar estadísticas del atleta
        statistic_controller.update_athlete_stats(db, existing.athlete_id)
        return True

    def list_tests(
        self, db: Session, filters: SprintTestFilter
    ) -> tuple[list[SprintTest], int]:
        """Listar Sprint Tests con paginación y filtros básicos."""
        query = db.query(SprintTest).filter(SprintTest.is_active)

        if filters.evaluation_id:
            query = query.filter(SprintTest.evaluation_id == filters.evaluation_id)
        if filters.athlete_id:
            query = query.filter(SprintTest.athlete_id == filters.athlete_id)

        total = query.with_entities(func.count()).scalar() or 0

        items = (
            query.order_by(desc(SprintTest.date))
            .offset(filters.skip)
            .limit(filters.limit)
            .all()
        )

        return items, total
