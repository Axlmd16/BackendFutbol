from typing import List, Optional

from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.evaluator import Evaluator


class EvaluatorDAO(BaseDAO[Evaluator]):
    """DAO específico para evaluadores."""

    def __init__(self):
        super().__init__(Evaluator)

    def get_by_dni(
        self,
        db: Session,
        dni: str,
        only_active: bool = True
    ) -> Optional[Evaluator]:
        """Obtener un evaluador por DNI sin exponer lógica de búsqueda genérica."""
        return self.get_by_field(db, "dni", dni, only_active)

    def get_by_ids(
        self,
        db: Session,
        evaluator_ids: List[int],
        only_active: bool = True
    ) -> List[Evaluator]:
        """Recuperar múltiples evaluadores (útil para precargar sujetos ligados a tokens)."""
        if not evaluator_ids:
            return []

        query = db.query(self.model).filter(self.model.id.in_(evaluator_ids))
        if only_active:
            query = query.filter(self.model.is_active == True)
        return query.all()
