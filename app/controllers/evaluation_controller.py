"""Controller para gestión de Evaluaciones."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.dao.athlete_dao import AthleteDAO
from app.dao.evaluation_dao import EvaluationDAO
from app.dao.test_dao import TestDAO
from app.models.evaluation import Evaluation
from app.models.test import Test
from app.utils.exceptions import DatabaseException


class EvaluationController:
    """Controlador para lógica de negocio de Evaluaciones."""

    def __init__(self):
        self.evaluation_dao = EvaluationDAO()
        self.test_dao = TestDAO()
        self.athlete_dao = AthleteDAO()

    # ==================== CRUD EVALUATIONS ====================

    def create_evaluation(
        self,
        db: Session,
        name: str,
        date: datetime,
        time: str,
        user_id: int,
        location: Optional[str] = None,
        observations: Optional[str] = None,
    ) -> Evaluation:
        """Crear una nueva evaluación.

        Args:
            db: Sesión de base de datos
            name: Nombre de la evaluación
            date: Fecha y hora
            time: Hora en formato HH:MM
            user_id: ID del evaluador
            location: Ubicación opcional
            observations: Observaciones generales

        Returns:
            La evaluación creada

        Raises:
            DatabaseException: Si hay errores de validación o BD
        """
        return self.evaluation_dao.create(
            db=db,
            name=name,
            date=date,
            time=time,
            user_id=user_id,
            location=location,
            observations=observations,
        )

    def get_evaluation(self, db: Session, evaluation_id: int) -> Optional[Evaluation]:
        """Obtener una evaluación por ID.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación

        Returns:
            La evaluación o None
        """
        return self.evaluation_dao.get_by_id(db, evaluation_id)

    def list_evaluations(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[Evaluation]:
        """Listar todas las evaluaciones.

        Args:
            db: Sesión de base de datos
            skip: Registros a saltar
            limit: Límite de registros

        Returns:
            Lista de evaluaciones
        """
        return self.evaluation_dao.list_all(db, skip, limit)

    def list_evaluations_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Evaluation]:
        """Listar evaluaciones de un usuario específico.

        Args:
            db: Sesión de base de datos
            user_id: ID del evaluador
            skip: Registros a saltar
            limit: Límite de registros

        Returns:
            Lista de evaluaciones del usuario
        """
        return self.evaluation_dao.list_by_user(db, user_id, skip, limit)

    def update_evaluation(
        self,
        db: Session,
        evaluation_id: int,
        name: Optional[str] = None,
        date: Optional[datetime] = None,
        time: Optional[str] = None,
        location: Optional[str] = None,
        observations: Optional[str] = None,
    ) -> Optional[Evaluation]:
        """Actualizar una evaluación existente.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación
            name: Nuevo nombre (opcional)
            date: Nueva fecha (opcional)
            time: Nueva hora (opcional)
            location: Nueva ubicación (opcional)
            observations: Nuevas observaciones (opcional)

        Returns:
            La evaluación actualizada o None
        """
        return self.evaluation_dao.update(
            db=db,
            evaluation_id=evaluation_id,
            name=name,
            date=date,
            time=time,
            location=location,
            observations=observations,
        )

    def delete_evaluation(self, db: Session, evaluation_id: int) -> bool:
        """Eliminar una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación

        Returns:
            True si fue eliminada, False si no existe
        """
        return self.evaluation_dao.delete(db, evaluation_id)

    # ==================== TEST MANAGEMENT ====================

    def add_sprint_test(
        self,
        db: Session,
        evaluation_id: int,
        athlete_id: int,
        date: datetime,
        distance_meters: float,
        time_0_10_s: float,
        time_0_30_s: float,
        observations: Optional[str] = None,
    ) -> Test:
        """Agregar un Sprint Test a una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación
            athlete_id: ID del atleta
            date: Fecha del test
            distance_meters: Distancia en metros
            time_0_10_s: Tiempo 0-10 metros
            time_0_30_s: Tiempo 0-30 metros
            observations: Observaciones opcionales

        Returns:
            El test creado
        """
        # Validar que la evaluación y atleta existan
        self._validate_evaluation_exists(db, evaluation_id)
        self._validate_athlete_exists(db, athlete_id)

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

    def add_yoyo_test(
        self,
        db: Session,
        evaluation_id: int,
        athlete_id: int,
        date: datetime,
        shuttle_count: int,
        final_level: str,
        failures: int,
        observations: Optional[str] = None,
    ) -> Test:
        """Agregar un Yoyo Test a una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación
            athlete_id: ID del atleta
            date: Fecha del test
            shuttle_count: Número de shuttles
            final_level: Nivel final
            failures: Número de fallos
            observations: Observaciones opcionales

        Returns:
            El test creado
        """
        self._validate_evaluation_exists(db, evaluation_id)
        self._validate_athlete_exists(db, athlete_id)

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

    def add_endurance_test(
        self,
        db: Session,
        evaluation_id: int,
        athlete_id: int,
        date: datetime,
        min_duration: int,
        total_distance_m: float,
        observations: Optional[str] = None,
    ) -> Test:
        """Agregar un Endurance Test a una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación
            athlete_id: ID del atleta
            date: Fecha del test
            min_duration: Duración en minutos
            total_distance_m: Distancia total en metros
            observations: Observaciones opcionales

        Returns:
            El test creado
        """
        self._validate_evaluation_exists(db, evaluation_id)
        self._validate_athlete_exists(db, athlete_id)

        return self.test_dao.create_endurance_test(
            db=db,
            date=date,
            athlete_id=athlete_id,
            evaluation_id=evaluation_id,
            min_duration=min_duration,
            total_distance_m=total_distance_m,
            observations=observations,
        )

    def add_technical_assessment(
        self,
        db: Session,
        evaluation_id: int,
        athlete_id: int,
        date: datetime,
        ball_control: Optional[str] = None,
        short_pass: Optional[str] = None,
        long_pass: Optional[str] = None,
        shooting: Optional[str] = None,
        dribbling: Optional[str] = None,
        observations: Optional[str] = None,
    ) -> Test:
        """Agregar una Technical Assessment a una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación
            athlete_id: ID del atleta
            date: Fecha del test
            ball_control: Evaluación de control
            short_pass: Evaluación de pases cortos
            long_pass: Evaluación de pases largos
            shooting: Evaluación de disparo
            dribbling: Evaluación de regate
            observations: Observaciones opcionales

        Returns:
            El test creado
        """
        self._validate_evaluation_exists(db, evaluation_id)
        self._validate_athlete_exists(db, athlete_id)

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

    def list_tests_by_evaluation(self, db: Session, evaluation_id: int) -> List[Test]:
        """Listar todos los tests de una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación

        Returns:
            Lista de tests
        """
        self._validate_evaluation_exists(db, evaluation_id)
        return self.test_dao.list_by_evaluation(db, evaluation_id)

    def delete_test(self, db: Session, test_id: int) -> bool:
        """Eliminar un test.

        Args:
            db: Sesión de base de datos
            test_id: ID del test

        Returns:
            True si fue eliminado, False si no existe
        """
        return self.test_dao.delete(db, test_id)

    # ==================== VALIDACIONES ====================

    @staticmethod
    def _validate_evaluation_exists(db: Session, evaluation_id: int) -> None:
        """Validar que una evaluación existe.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación

        Raises:
            DatabaseException: Si no existe
        """
        evaluation_dao = EvaluationDAO()
        if not evaluation_dao.get_by_id(db, evaluation_id):
            raise DatabaseException(f"Evaluación {evaluation_id} no existe")

    @staticmethod
    def _validate_athlete_exists(db: Session, athlete_id: int) -> None:
        """Validar que un atleta existe.

        Args:
            db: Sesión de base de datos
            athlete_id: ID del atleta

        Raises:
            DatabaseException: Si no existe
        """
        athlete_dao = AthleteDAO()
        if not athlete_dao.get_by_id(db, athlete_id):
            raise DatabaseException(f"Atleta {athlete_id} no existe")
