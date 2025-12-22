from fastapi import APIRouter

from app.controllers.endurance_test_controller import EnduranceTestController

router = APIRouter(prefix="/endurance-tests", tags=["EnduranceTests"])
endurance_test_controller = EnduranceTestController()
