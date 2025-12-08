from app.controllers.athlete_controller import AthleteController
from app.controllers.test_controller import TestController
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/tests", tags=["Tests"])
test_controller = TestController()