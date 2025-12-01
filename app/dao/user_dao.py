from app.dao.base import BaseDAO
from app.models.user import User
from sqlalchemy.orm import Session
from typing import Optional, List

class UserDAO(BaseDAO[User]):
    """
    DAO específico para usuarios
    Hereda TODAS las operaciones CRUD del BaseDAO
    Solo agrega métodos específicos de usuario
    """
    
    def __init__(self):
        super().__init__(User)
    
    # ==================== MÉTODOS ESPECÍFICOS DE USUARIO ====================
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Obtener usuario por email (usa método heredado)"""
        return self.get_by_field(db, "email", email)
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Obtener usuario por username (usa método heredado)"""
        return self.get_by_field(db, "username", username)
    
    def email_exists(self, db: Session, email: str, exclude_id: Optional[int] = None) -> bool:
        """Verificar si un email ya está registrado"""
        user = self.get_by_email(db, email)
        if not user:
            return False
        if exclude_id and user.id == exclude_id:
            return False
        return True
    
    def username_exists(self, db: Session, username: str, exclude_id: Optional[int] = None) -> bool:
        """Verificar si un username ya está registrado"""
        user = self.get_by_username(db, username)
        if not user:
            return False
        if exclude_id and user.id == exclude_id:
            return False
        return True
    
    def get_active_users(self, db: Session) -> List[User]:
        """Obtener solo usuarios activos (usa método heredado)"""
        return self.get_all_by_field(db, "is_active", True)
    
    def activate_user(self, db: Session, user_id: int) -> Optional[User]:
        """Activar un usuario inactivo"""
        return self.update(db, user_id, {"is_active": True})
    
    def deactivate_user(self, db: Session, user_id: int) -> Optional[User]:
        """Desactivar un usuario"""
        return self.update(db, user_id, {"is_active": False})