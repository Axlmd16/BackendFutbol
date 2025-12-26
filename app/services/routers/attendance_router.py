from fastapi import APIRouter

from app.controllers.attendance_controller import AttendanceController

router = APIRouter(prefix="/attendances", tags=["Attendances"])
attendance_controller = AttendanceController()
