from app.dao.base import BaseDAO
from app.models.endurance_test import EnduranceTest


class EnduranceTestDAO(BaseDAO[EnduranceTest]):
    """DAO específico para pruebas de resistencia."""

    def __init__(self):
        super().__init__(EnduranceTest)
