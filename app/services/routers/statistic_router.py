from fastapi import APIRouter

from app.controllers.statistic_controller import StatisticController

router = APIRouter(prefix="/statistics", tags=["Statistics"])
statistic_controller = StatisticController()
