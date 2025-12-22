from fastapi import APIRouter

from app.controllers.evaluation_controller import EvaluationController

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])
evaluation_controller = EvaluationController()
