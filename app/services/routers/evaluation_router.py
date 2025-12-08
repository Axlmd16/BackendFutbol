from app.controllers.evaluation_controller import EvaluationController
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])
evaluation_controller = EvaluationController()
