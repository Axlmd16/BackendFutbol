from app.controllers.yoyo_test_controller import YoyoTestController
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/yoyo-tests", tags=["YoyoTests"])
yoyo_test_controller = YoyoTestController()
