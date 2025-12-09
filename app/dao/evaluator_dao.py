from typing import List, Optional

from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.evaluator import Evaluator


# DAO específico para evaluadores
class EvaluatorDAO(BaseDAO[Evaluator]):
    """DAO específico para evaluadores."""
   
    # Inicializador
    def __init__(self):
        super().__init__(Evaluator)
    

    # Obtener un evaluador por su DNI
    def get_by_dni(
        self,
        db: Session,
        dni: str,
        only_active: bool = True
    ) -> Optional[Evaluator]:
        return self.get_by_field(db, "dni", dni, only_active)



    # Obtener múltiples evaluadores por una lista de IDs
    def get_by_ids(
        self,
        db: Session,
        evaluator_ids: List[int],
        only_active: bool = True
    ) -> List[Evaluator]:
        if not evaluator_ids:
            return []

        query = db.query(self.model).filter(self.model.id.in_(evaluator_ids))
        if only_active:
            query = query.filter(self.model.is_active == True)
        return query.all()
