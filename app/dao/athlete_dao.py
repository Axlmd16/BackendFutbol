from app.dao.base import BaseDAO
from app.models.athlete import Athlete

class AthleteDAO(BaseDAO[Athlete]):
    """
    DAO específico para deportistas
    """
    
    def __init__(self):
        super().__init__(Athlete)