from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.dao.evaluator_dao import EvaluatorDAO
from app.models.evaluator import Evaluator


class EvaluatorController:
    """Controlador de evaluadores."""

    def __init__(self):
        self.evaluator_dao = EvaluatorDAO()
   

    # Listar evaluadores con paginación básica
    def list(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True
    ) -> List[Evaluator]:
        return self.evaluator_dao.get_all(db, skip=skip, limit=limit, only_active=only_active)
  

    # Obtener un evaluador por ID
    def get(
        self,
        db: Session,
        evaluator_id: int,
        *,
        only_active: bool = True
    ) -> Optional[Evaluator]:
        return self.evaluator_dao.get_by_id(db, evaluator_id, only_active)


    # Crear un nuevo evaluador delegando en el DAO
    def create(self, db: Session, data: Dict[str, Any]) -> Evaluator:
        return self.evaluator_dao.create(db, data)
 

    # Actualizar un evaluador existente
    def update(
        self,
        db: Session,
        evaluator_id: int,
        data: Dict[str, Any]
    ) -> Optional[Evaluator]:
        return self.evaluator_dao.update(db, evaluator_id, data)


    # Eliminar (o desactivar) un evaluador
    def delete(
        self,
        db: Session,
        evaluator_id: int,
        *,
        soft_delete: bool = True
    ) -> bool:
        return self.evaluator_dao.delete(db, evaluator_id, soft_delete)

    # Obtener un evaluador por DNI
    def get_by_dni(
        self,
        db: Session,
        dni: str,
        *,
        only_active: bool = True
    ) -> Optional[Evaluator]:
        return self.evaluator_dao.get_by_dni(db, dni, only_active)

    # Obtener múltiples evaluadores por una lista de IDs
    def get_by_ids(
        self,
        db: Session,
        evaluator_ids: List[int],
        *,
        only_active: bool = True
    ) -> List[Evaluator]:
        return self.evaluator_dao.get_by_ids(db, evaluator_ids, only_active)
