from fastapi import APIRouter

from app.controllers.sprint_test_controller import SprintTestController

router = APIRouter(prefix="/sprint-tests", tags=["SprintTests"])
sprint_test_controller = SprintTestController()
