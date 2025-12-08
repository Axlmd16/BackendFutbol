from app.controllers.endurance_test_controller import EnduranceTestController
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/endurance-tests", tags=["EnduranceTests"])
endurance_test_controller = EnduranceTestController()
