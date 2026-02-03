"""DAO para gestión de Tests (pruebas)."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.endurance_test import EnduranceTest
from app.models.sprint_test import SprintTest
from app.models.technical_assessment import TechnicalAssessment
from app.models.test import Test
from app.models.yoyo_test import YoyoTest
from app.utils.exceptions import DatabaseException


class TestDAO(BaseDAO[Test]):
    """DAO para operaciones CRUD en Tests (pruebas polimórficas)."""

    __test__ = False  # evitar que pytest lo tome como test

    def __init__(self):
        super().__init__(Test)

    # ==================== FACTORY METHODS ====================

    def create_sprint_test(
        self,
        db: Session,
        date: datetime,
        athlete_id: int,
        evaluation_id: int,
        distance_meters: float,
        time_0_10_s: float,
        time_0_30_s: float,
        observations: Optional[str] = None,
    ) -> SprintTest:
        """Crear una prueba de sprint (velocidad).

        Args:
            db: Sesión de base de datos
            date: Fecha del test
            athlete_id: ID del atleta
            evaluation_id: ID de la evaluación
            distance_meters: Distancia en metros
            time_0_10_s: Tiempo 0-10 metros
            time_0_30_s: Tiempo 0-30 metros
            observations: Observaciones opcionales

        Returns:
            El SprintTest creado
        """
        try:
            self._validate_test_data(athlete_id, evaluation_id, date)

            test = SprintTest(
                date=date,
                athlete_id=athlete_id,
                evaluation_id=evaluation_id,
                distance_meters=distance_meters,
                time_0_10_s=time_0_10_s,
                time_0_30_s=time_0_30_s,
                observations=observations,
            )

            db.add(test)
            db.commit()
            db.refresh(test)
            return test

        except DatabaseException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error al crear SprintTest: {str(e)}") from e

    def create_yoyo_test(
        self,
        db: Session,
        date: datetime,
        athlete_id: int,
        evaluation_id: int,
        shuttle_count: int,
        final_level: str,
        failures: int,
        observations: Optional[str] = None,
    ) -> YoyoTest:
        """Crear una prueba Yoyo (resistencia aerobia).

        Args:
            db: Sesión de base de datos
            date: Fecha del test
            athlete_id: ID del atleta
            evaluation_id: ID de la evaluación
            shuttle_count: Número de shuttles completados
            final_level: Nivel final (ej: 16.3, 18.2)
            failures: Número de fallos
            observations: Observaciones opcionales

        Returns:
            El YoyoTest creado
        """
        try:
            self._validate_test_data(athlete_id, evaluation_id, date)

            test = YoyoTest(
                date=date,
                athlete_id=athlete_id,
                evaluation_id=evaluation_id,
                shuttle_count=shuttle_count,
                final_level=final_level,
                failures=failures,
                observations=observations,
            )

            db.add(test)
            db.commit()
            db.refresh(test)
            return test

        except DatabaseException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error al crear YoyoTest: {str(e)}") from e

    def create_endurance_test(
        self,
        db: Session,
        date: datetime,
        athlete_id: int,
        evaluation_id: int,
        min_duration: int,
        total_distance_m: float,
        observations: Optional[str] = None,
    ) -> EnduranceTest:
        """Crear una prueba de resistencia.

        Args:
            db: Sesión de base de datos
            date: Fecha del test
            athlete_id: ID del atleta
            evaluation_id: ID de la evaluación
            min_duration: Duración en minutos
            total_distance_m: Distancia total en metros
            observations: Observaciones opcionales

        Returns:
            El EnduranceTest creado
        """
        try:
            self._validate_test_data(athlete_id, evaluation_id, date)

            test = EnduranceTest(
                date=date,
                athlete_id=athlete_id,
                evaluation_id=evaluation_id,
                min_duration=min_duration,
                total_distance_m=total_distance_m,
                observations=observations,
            )

            db.add(test)
            db.commit()
            db.refresh(test)
            return test

        except DatabaseException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error al crear EnduranceTest: {str(e)}") from e

    def create_technical_assessment(
        self,
        db: Session,
        date: datetime,
        athlete_id: int,
        evaluation_id: int,
        ball_control: Optional[str] = None,
        short_pass: Optional[str] = None,
        long_pass: Optional[str] = None,
        shooting: Optional[str] = None,
        dribbling: Optional[str] = None,
        observations: Optional[str] = None,
    ) -> TechnicalAssessment:
        """Crear una evaluación técnica.

        Args:
            db: Sesión de base de datos
            date: Fecha del test
            athlete_id: ID del atleta
            evaluation_id: ID de la evaluación
            ball_control: Evaluación de control de balón
            short_pass: Evaluación de pases cortos
            long_pass: Evaluación de pases largos
            shooting: Evaluación de disparo
            dribbling: Evaluación de regate
            observations: Observaciones opcionales

        Returns:
            El TechnicalAssessment creado
        """
        try:
            self._validate_test_data(athlete_id, evaluation_id, date)

            test = TechnicalAssessment(
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

            db.add(test)
            db.commit()
            db.refresh(test)
            return test

        except DatabaseException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Error al crear TechnicalAssessment: {str(e)}"
            ) from e

    # ==================== QUERY METHODS ====================

    def get_by_id(
        self, db: Session, test_id: int, only_active: bool = True
    ) -> Optional[Test]:
        """Obtener un test por ID."""
        try:
            query = db.query(Test).filter(Test.id == test_id)
            if only_active:
                query = query.filter(Test.is_active)
            return query.first()
        except Exception as e:
            raise DatabaseException(f"Error al obtener test {test_id}: {str(e)}") from e

    def list_by_evaluation(
        self, db: Session, evaluation_id: int, only_active: bool = True
    ) -> List[Test]:
        """Listar todos los tests de una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación
            only_active: Filtrar solo activos

        Returns:
            Lista de tests de la evaluación
        """
        try:
            query = db.query(Test).filter(Test.evaluation_id == evaluation_id)
            if only_active:
                query = query.filter(Test.is_active)
            return query.all()
        except Exception as e:
            raise DatabaseException(
                f"Error al listar tests de evaluación {evaluation_id}: {str(e)}"
            ) from e

    def list_by_athlete(
        self, db: Session, athlete_id: int, only_active: bool = True
    ) -> List[Test]:
        """Listar todos los tests de un atleta.

        Args:
            db: Sesión de base de datos
            athlete_id: ID del atleta
            only_active: Filtrar solo activos

        Returns:
            Lista de tests del atleta
        """
        try:
            query = db.query(Test).filter(Test.athlete_id == athlete_id)
            if only_active:
                query = query.filter(Test.is_active)
            return query.all()
        except Exception as e:
            raise DatabaseException(
                f"Error al listar tests del atleta {athlete_id}: {str(e)}"
            ) from e

    def count_by_evaluation(self, db: Session, evaluation_id: int) -> int:
        """Contar tests de una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación

        Returns:
            Cantidad de tests
        """
        try:
            return (
                db.query(Test)
                .filter(Test.evaluation_id == evaluation_id, Test.is_active)
                .count()
            )
        except Exception as e:
            raise DatabaseException(
                f"Error al contar tests de evaluación {evaluation_id}: {str(e)}"
            ) from e

    def delete(self, db: Session, test_id: int) -> bool:
        """Eliminar (soft delete) un test.

        Args:
            db: Sesión de base de datos
            test_id: ID del test a eliminar

        Returns:
            True si fue eliminado, False si no existe
        """
        try:
            test = self.get_by_id(db, test_id, only_active=True)
            if not test:
                return False

            test.is_active = False
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Error al eliminar test {test_id}: {str(e)}"
            ) from e

    # ==================== VALIDACIONES ====================

    @staticmethod
    def _validate_test_data(
        athlete_id: int, evaluation_id: int, date: datetime
    ) -> None:
        """Validar datos básicos del test.

        Args:
            athlete_id: ID del atleta
            evaluation_id: ID de la evaluación
            date: Fecha del test

        Raises:
            DatabaseException: Si hay validación fallida
        """
        if not athlete_id or athlete_id <= 0:
            raise DatabaseException("athlete_id inválido")

        if not evaluation_id or evaluation_id <= 0:
            raise DatabaseException("evaluation_id inválido")

        if not date:
            raise DatabaseException("La fecha del test es requerida")
