from app.dao.base import BaseDAO
from app.models.test import Test


class TestDAO(BaseDAO[Test]):
    """DAO específico para pruebas base (polimórficas)."""

    __test__ = False  # evitar que pytest lo tome como test

    def __init__(self):
        super().__init__(Test)
