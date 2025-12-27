from app.dao.base import BaseDAO
from app.models.athlete import Athlete
from sqlalchemy.orm import Session
from typing import Optional
import logging


class AthleteDAO(BaseDAO[Athlete]):
    """
    DAO específico para deportistas.
    
    Gestiona operaciones de base de datos relacionadas con
    atletas, incluyendo menores de edad con representantes legales.
    """

    def __init__(self):
        super().__init__(Athlete)
