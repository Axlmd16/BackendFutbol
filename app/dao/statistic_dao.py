from app.dao.base import BaseDAO
from app.models.statistic import Statistic


class StatisticDAO(BaseDAO[Statistic]):
    """DAO específico para estadísticas de atletas."""

    def __init__(self):
        super().__init__(Statistic)
