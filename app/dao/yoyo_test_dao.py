from app.dao.base import BaseDAO
from app.models.yoyo_test import YoyoTest


class YoyoTestDAO(BaseDAO[YoyoTest]):
    """DAO específico para pruebas Yo-Yo."""

    def __init__(self):
        super().__init__(YoyoTest)
