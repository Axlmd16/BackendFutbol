from app.dao.base import BaseDAO
from app.models.athlete import Athlete
from sqlalchemy.orm import Session
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AthleteDAO(BaseDAO[Athlete]):
    """
    DAO específico para deportistas.
    
    Gestiona operaciones de base de datos relacionadas con
    atletas, incluyendo menores de edad con representantes legales.
    """
    
    def __init__(self):
        super().__init__(Athlete)
    
    def get_by_dni(
        self, 
        db: Session, 
        dni: str,
        only_active: bool = True
    ) -> Optional[Athlete]:
        """
        Obtiene un deportista por su DNI.
        
        Args:
            db: Sesión de base de datos
            dni: Documento de identidad del deportista
            only_active: Si True, solo busca deportistas activos
            
        Returns:
            Deportista encontrado o None
        """
        return self.get_by_field(db, "dni", dni, only_active)
