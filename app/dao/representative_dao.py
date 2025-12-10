from app.dao.base import BaseDAO
from app.models.representative import Representative
from sqlalchemy.orm import Session
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RepresentativeDAO(BaseDAO[Representative]):
    """
    DAO específico para representantes legales.
    
    Gestiona operaciones de base de datos relacionadas con
    tutores o padres de deportistas menores de edad.
    """

    def __init__(self):
        super().__init__(Representative)
    
    def get_by_dni(
        self, 
        db: Session, 
        dni: str,
        only_active: bool = True
    ) -> Optional[Representative]:
        """
        Obtiene un representante por su DNI.
        
        Args:
            db: Sesión de base de datos
            dni: Documento de identidad del representante
            only_active: Si True, solo busca representantes activos
            
        Returns:
            Representante encontrado o None
        """
        return self.get_by_field(db, "dni", dni, only_active)
    
    def get_by_email(
        self, 
        db: Session, 
        email: str,
        only_active: bool = True
    ) -> Optional[Representative]:
        """
        Obtiene un representante por su correo electrónico.
        
        Args:
            db: Sesión de base de datos
            email: Correo electrónico del representante
            only_active: Si True, solo busca representantes activos
            
        Returns:
            Representante encontrado o None
        """
        return self.get_by_field(db, "email", email, only_active)
