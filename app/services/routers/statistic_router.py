from app.controllers.statistic_controller import StatisticController
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/statistics", tags=["Statistics"])
statistic_controller = StatisticController()
