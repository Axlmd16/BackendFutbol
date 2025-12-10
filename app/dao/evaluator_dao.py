from app.dao.base import BaseDAO
from app.models.evaluator import Evaluator


class EvaluatorDAO(BaseDAO[Evaluator]):
    """DAO específico para evaluadores."""

    def __init__(self):
        super().__init__(Evaluator)
