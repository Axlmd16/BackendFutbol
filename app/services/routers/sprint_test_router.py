from app.controllers.sprint_test_controller import SprintTestController
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/sprint-tests", tags=["SprintTests"])
sprint_test_controller = SprintTestController()
