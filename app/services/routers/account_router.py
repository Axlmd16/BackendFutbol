from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.controllers.account_controller import AccountController
from app.core.database import get_db
from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException

router = APIRouter(prefix="/accounts", tags=["Accounts"])
account_controller = AccountController()


