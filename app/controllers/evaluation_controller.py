"""Controller para gestión de Evaluaciones."""

import re
from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.dao.evaluation_dao import EvaluationDAO
from app.models.evaluation import Evaluation
from app.schemas.evaluation_schema import (
    CreateEvaluationSchema,
    EvaluationFilter,
    UpdateEvaluationSchema,
)
from app.utils.exceptions import DatabaseException


class EvaluationController:
    """Controlador para CRUD de Evaluaciones."""

    def __init__(self):
        self.evaluation_dao = EvaluationDAO()

    # ==================== CRUD EVALUATIONS ====================

    def create_evaluation(
        self,
        db: Session,
        payload: CreateEvaluationSchema,
    ) -> Evaluation:
        """Crear una nueva evaluación."""

        return self.evaluation_dao.create(
            db=db,
            name=payload.name,
            date=payload.date,
            time=payload.time,
            user_id=payload.user_id,
            location=payload.location,
            observations=payload.observations,
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

    def list_evaluations_paginated(
        self, db: Session, filters: EvaluationFilter
    ) -> tuple[list[Evaluation], int]:
        """Listar evaluaciones con paginación y filtros básicos."""
        query = db.query(Evaluation).filter(Evaluation.is_active)

        if filters.user_id:
            query = query.filter(Evaluation.user_id == filters.user_id)

        if filters.search:
            like = f"%{filters.search.strip()}%"
            query = query.filter(Evaluation.name.ilike(like))

        if filters.date:
            # Filtrar por fecha (solo la parte de fecha, sin hora)
            query = query.filter(func.date(Evaluation.date) == filters.date)

        if filters.location:
            like = f"%{filters.location.strip()}%"
            query = query.filter(Evaluation.location.ilike(like))

        total = query.with_entities(func.count()).scalar() or 0

        items = (
            query.order_by(desc(Evaluation.date))
            .offset(filters.skip)
            .limit(filters.limit)
            .all()
        )

        return items, total

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
        self, db: Session, evaluation_id: int, payload: UpdateEvaluationSchema
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
        if payload.date is not None and not isinstance(payload.date, datetime):
            raise DatabaseException("La fecha de evaluación es inválida")

        if payload.time is not None:
            if not re.match(r"^\d{2}:\d{2}$", payload.time or ""):
                raise DatabaseException("La hora de evaluación es inválida")
            hour, minute = map(int, payload.time.split(":"))
            if hour not in range(24) or minute not in range(60):
                raise DatabaseException("La hora de evaluación es inválida")

        return self.evaluation_dao.update(
            db=db,
            evaluation_id=evaluation_id,
            name=payload.name,
            date=payload.date,
            time=payload.time,
            location=payload.location,
            observations=payload.observations,
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
