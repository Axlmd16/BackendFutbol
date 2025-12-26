from fastapi import APIRouter

from app.controllers.athlete_controller import AthleteController

router = APIRouter(prefix="/athletes", tags=["Athletes"])
athlete_controller = AthleteController()
