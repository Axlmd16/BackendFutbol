from fastapi import APIRouter

from app.controllers.yoyo_test_controller import YoyoTestController

router = APIRouter(prefix="/yoyo-tests", tags=["YoyoTests"])
yoyo_test_controller = YoyoTestController()
