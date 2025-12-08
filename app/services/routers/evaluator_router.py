from app.controllers.evaluator_controller import EvaluatorController
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/evaluators", tags=["Evaluators"])
evaluator_controller = EvaluatorController()
