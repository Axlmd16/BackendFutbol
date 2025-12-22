from fastapi import APIRouter

from app.controllers.user_controller import UserController

router = APIRouter(prefix="/users", tags=["Users"])
user_controller = UserController()
