from app.dao.attendance_dao import AttendanceDAO


class AttendanceController:
    """Controlador de asistencias."""

    def __init__(self):
        self.attendance_dao = AttendanceDAO()
