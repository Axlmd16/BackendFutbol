"""DAO para gestión de Evaluaciones."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.evaluation import Evaluation
from app.utils.exceptions import DatabaseException


class EvaluationDAO(BaseDAO[Evaluation]):
    """DAO para operaciones CRUD en Evaluaciones."""

    def __init__(self):
        super().__init__(Evaluation)

    def create(
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
            user_id: ID del evaluador (usuario)
            location: Ubicación opcional
            observations: Observaciones generales

        Returns:
            La evaluación creada

        Raises:
            DatabaseException: Si hay error en la BD o validación falla
        """
        try:
            # Validaciones
            self._validate_date(date)
            self._validate_duplicate_evaluation(db, name, date, user_id)

            evaluation = Evaluation(
                name=name,
                date=date,
                time=time,
                user_id=user_id,
                location=location,
                observations=observations,
            )

            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)
            return evaluation

        except DatabaseException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error al crear evaluación: {str(e)}") from e

    def get_by_id(
        self, db: Session, evaluation_id: int, only_active: bool = True
    ) -> Optional[Evaluation]:
        """Obtener evaluación por ID.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación
            only_active: Filtrar solo activos

        Returns:
            La evaluación si existe, None en caso contrario
        """
        try:
            query = db.query(Evaluation).filter(Evaluation.id == evaluation_id)
            if only_active:
                query = query.filter(Evaluation.is_active)
            return query.first()
        except Exception as e:
            raise DatabaseException(
                f"Error al obtener evaluación {evaluation_id}: {str(e)}"
            ) from e

    def list_all(
        self, db: Session, skip: int = 0, limit: int = 100, only_active: bool = True
    ) -> List[Evaluation]:
        """Listar todas las evaluaciones con paginación.

        Args:
            db: Sesión de base de datos
            skip: Cantidad de registros a saltar
            limit: Cantidad máxima de registros
            only_active: Filtrar solo activos

        Returns:
            Lista de evaluaciones
        """
        try:
            query = db.query(Evaluation)
            if only_active:
                query = query.filter(Evaluation.is_active)

            # Ordenar por fecha descendente (más recientes primero)
            return query.order_by(desc(Evaluation.date)).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error al listar evaluaciones: {str(e)}") from e

    def list_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Evaluation]:
        """Listar evaluaciones de un usuario específico.

        Args:
            db: Sesión de base de datos
            user_id: ID del evaluador
            skip: Cantidad de registros a saltar
            limit: Cantidad máxima de registros

        Returns:
            Lista de evaluaciones del usuario
        """
        try:
            return (
                db.query(Evaluation)
                .filter(Evaluation.user_id == user_id, Evaluation.is_active)
                .order_by(desc(Evaluation.date))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            raise DatabaseException(
                f"Error al listar evaluaciones del usuario {user_id}: {str(e)}"
            ) from e

    def update(
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
            evaluation_id: ID de la evaluación a actualizar
            name: Nuevo nombre (opcional)
            date: Nueva fecha (opcional)
            time: Nueva hora (opcional)
            location: Nueva ubicación (opcional)
            observations: Nuevas observaciones (opcional)

        Returns:
            La evaluación actualizada, o None si no existe

        Raises:
            DatabaseException: Si hay error en la BD o validación falla
        """
        try:
            evaluation = self.get_by_id(db, evaluation_id, only_active=True)
            if not evaluation:
                return None

            # Validaciones
            if date:
                self._validate_date(date)

            # Actualizar solo los campos proporcionados
            if name is not None:
                evaluation.name = name
            if date is not None:
                evaluation.date = date
            if time is not None:
                evaluation.time = time
            if location is not None:
                evaluation.location = location
            if observations is not None:
                evaluation.observations = observations

            db.commit()
            db.refresh(evaluation)
            return evaluation

        except DatabaseException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Error al actualizar evaluación {evaluation_id}: {str(e)}"
            ) from e

    def delete(self, db: Session, evaluation_id: int) -> bool:
        """Eliminar (soft delete) una evaluación.

        Args:
            db: Sesión de base de datos
            evaluation_id: ID de la evaluación a eliminar

        Returns:
            True si fue eliminada, False si no existe
        """
        try:
            evaluation = self.get_by_id(db, evaluation_id, only_active=True)
            if not evaluation:
                return False

            evaluation.is_active = False
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Error al eliminar evaluación {evaluation_id}: {str(e)}"
            ) from e

    def count_evaluations(self, db: Session, only_active: bool = True) -> int:
        """Contar total de evaluaciones.

        Args:
            db: Sesión de base de datos
            only_active: Contar solo activos

        Returns:
            Cantidad de evaluaciones
        """
        try:
            query = db.query(Evaluation)
            if only_active:
                query = query.filter(Evaluation.is_active)
            return query.count()
        except Exception as e:
            raise DatabaseException(f"Error al contar evaluaciones: {str(e)}") from e

    # ==================== VALIDACIONES ====================

    @staticmethod
    def _validate_date(date: datetime) -> None:
        """Validar que la fecha no sea anterior a hoy.

        Args:
            date: Fecha a validar

        Raises:
            DatabaseException: Si la fecha es inválida
        """
        if date < datetime.now():
            raise DatabaseException(
                "La fecha de evaluación no puede ser anterior a hoy"
            )

    @staticmethod
    def _validate_duplicate_evaluation(
        db: Session, name: str, date: datetime, user_id: int
    ) -> None:
        """Validar que no exista una evaluación duplicada.

        Una evaluación se considera duplicada si tiene:
        - Mismo nombre
        - Misma fecha (mismo día)
        - Mismo evaluador

        Args:
            db: Sesión de base de datos
            name: Nombre de la evaluación
            date: Fecha de la evaluación
            user_id: ID del evaluador

        Raises:
            DatabaseException: Si existe una evaluación duplicada
        """
        existing = (
            db.query(Evaluation)
            .filter(
                Evaluation.name == name,
                func.date(Evaluation.date) == date.date(),
                Evaluation.user_id == user_id,
                Evaluation.is_active,
            )
            .first()
        )

        if existing:
            raise DatabaseException(
                f"Ya existe una evaluación con el nombre '{name}' "
                f"el {date.date()} por este evaluador"
            )
