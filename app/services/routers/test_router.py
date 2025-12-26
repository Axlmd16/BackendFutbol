from fastapi import APIRouter

from app.controllers.test_controller import TestController

router = APIRouter(prefix="/tests", tags=["Tests"])
test_controller = TestController()
