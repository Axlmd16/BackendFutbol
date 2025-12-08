from app.dao.base import BaseDAO
from app.models.evaluation import Evaluation


class EvaluationDAO(BaseDAO[Evaluation]):
    """DAO específico para evaluaciones."""

    def __init__(self):
        super().__init__(Evaluation)
