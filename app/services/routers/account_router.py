from fastapi import APIRouter

from app.controllers.account_controller import AccountController

router = APIRouter(prefix="/accounts", tags=["Accounts"])
account_controller = AccountController()
