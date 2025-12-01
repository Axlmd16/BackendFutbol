from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List, Optional

from app.dao.user_dao import UserDAO
from app.schemas.user_schema import UserCreate, UserUpdate
from app.models.user import User
from app.utils.exceptions import (
    AlreadyExistsException, 
    NotFoundException,
    UnauthorizedException,
    ValidationException
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserController:
    """
    Controlador de usuarios
    """
    
    def __init__(self):
        self.user_dao = UserDAO()
    
    # ==================== OPERACIONES CRUD ====================
    
    def get_all_users(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Obtener todos los usuarios"""
        return self.user_dao.get_all(db, skip, limit)
    
    def get_user_by_id(self, db: Session, user_id: int) -> User:
        """Obtener usuario por ID"""
        user = self.user_dao.get_by_id(db, user_id)
        if not user:
            raise NotFoundException("Usuario")
        return user
    
    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Crear un nuevo usuario"""
        # Validar email único
        if self.user_dao.email_exists(db, user_data.email):
            raise AlreadyExistsException("Email ya registrado")
        
        # # Validar username único
        if self.user_dao.username_exists(db, user_data.username):
            raise AlreadyExistsException("Username ya registrado")
        
        # Preparar datos
        user_dict = user_data.model_dump(exclude={"password"})
        
        user_dict["hashed_password"] = self._hash_password(user_data.password)
        
        # Crear usuario usando DAO
        return self.user_dao.create(db, user_dict)
    
    def update_user(
        self, 
        db: Session, 
        user_id: int, 
        user_data: UserUpdate
    ) -> User:
        """Actualizar un usuario"""
        # Verificar que existe
        existing_user = self.get_user_by_id(db, user_id)
        
        # Preparar datos
        update_dict = user_data.model_dump(exclude_unset=True, exclude={"password"})
        
        # Validar email si se está actualizando
        if "email" in update_dict:
            if self.user_dao.email_exists(db, update_dict["email"], exclude_id=user_id):
                raise AlreadyExistsException("Email")
        
        # Validar username si se está actualizando
        if "username" in update_dict:
            if self.user_dao.username_exists(db, update_dict["username"], exclude_id=user_id):
                raise AlreadyExistsException("Username")
        
        # Hash de password si se está actualizando
        if user_data.password:
            update_dict["hashed_password"] = self._hash_password(user_data.password)
        
        # Actualizar usando DAO
        updated = self.user_dao.update(db, user_id, update_dict)
        if not updated:
            raise NotFoundException("Usuario")
        
        return updated
    
    def delete_user(
        self, 
        db: Session, 
        user_id: int, 
        soft_delete: bool = True
    ) -> bool:
        """Eliminar un usuario"""
        deleted = self.user_dao.delete(db, user_id, soft_delete)
        if not deleted:
            raise NotFoundException("Usuario")
        return deleted
    
    # ==================== OPERACIONES ESPECÍFICAS ====================
    
    def authenticate_user(self, db: Session, email: str, password: str) -> User:
        """Autenticar un usuario"""
        user = self.user_dao.get_by_email(db, email)
        
        if not user:
            raise UnauthorizedException("Credenciales incorrectas")
        
        if not self._verify_password(password, user.hashed_password):
            raise UnauthorizedException("Credenciales incorrectas")
        
        if not user.is_active:
            raise UnauthorizedException("Usuario inactivo")
        
        return user
    
    def get_active_users(self, db: Session) -> List[User]:
        """Obtener usuarios activos"""
        return self.user_dao.get_active_users(db)
    
    def search_users(
        self,
        db: Session,
        email: Optional[str] = None,
        username: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Buscar usuarios con filtros"""
        filters = {}
        if email:
            filters["email"] = email
        if username:
            filters["username"] = username
        
        return self.user_dao.search(db, filters, skip=skip, limit=limit)
    
    def get_user_count(self, db: Session, only_active: bool = True) -> int:
        """Obtener cantidad de usuarios"""
        return self.user_dao.count(db, only_active)
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    def _hash_password(self, password: str) -> str:
        """Hash password con truncado seguro bcrypt"""
        if len(password.encode('utf-8')) > 72:
            password = password.encode('utf-8')[:72].decode('utf-8')
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return pwd_context.verify(plain_password, hashed_password)