from app.dao.base import BaseDAO
from app.models.sprint_test import SprintTest


class SprintTestDAO(BaseDAO[SprintTest]):
    """DAO específico para pruebas de sprint."""

    def __init__(self):
        super().__init__(SprintTest)
