from app.controllers.attendance_controller import AttendanceController
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/attendances", tags=["Attendances"])
attendance_controller = AttendanceController()
