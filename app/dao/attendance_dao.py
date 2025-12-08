from app.dao.base import BaseDAO
from app.models.attendance import Attendance


class AttendanceDAO(BaseDAO[Attendance]):
    """DAO específico para asistencias."""

    def __init__(self):
        super().__init__(Attendance)
