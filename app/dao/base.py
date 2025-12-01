from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from app.models.base import BaseModel
from app.utils.exceptions import DatabaseException
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseDAO(Generic[ModelType]):
    """
    DAO Genérico con TODAS las operaciones CRUD
    Cualquier DAO específico hereda de esta clase
    NO necesita interfaces porque Python usa duck typing
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    # ==================== OPERACIONES BÁSICAS ====================
    
    def get_all(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        only_active: bool = True
    ) -> List[ModelType]:
        """Obtener todos los registros con paginación"""
        try:
            query = db.query(self.model)
            if only_active:
                query = query.filter(self.model.is_active == True)
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Error al obtener registros")
    
    def get_by_id(
        self, 
        db: Session, 
        id: int, 
        only_active: bool = True
    ) -> Optional[ModelType]:
        """Obtener un registro por ID"""
        try:
            query = db.query(self.model).filter(self.model.id == id)
            if only_active:
                query = query.filter(self.model.is_active == True)
            return query.first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {str(e)}")
            raise DatabaseException(f"Error al obtener registro")
    
    def create(self, db: Session, obj_data: Dict[str, Any]) -> ModelType:
        """Crear un nuevo registro"""
        try:
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Error al crear registro")
    
    def update(
        self, 
        db: Session, 
        id: int, 
        obj_data: Dict[str, Any],
        exclude_none: bool = True
    ) -> Optional[ModelType]:
        """Actualizar un registro existente"""
        try:
            db_obj = self.get_by_id(db, id, only_active=False)
            if not db_obj:
                return None
            
            for key, value in obj_data.items():
                if exclude_none and value is None:
                    continue
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__} {id}: {str(e)}")
            raise DatabaseException(f"Error al actualizar registro")
    
    def delete(
        self, 
        db: Session, 
        id: int, 
        soft_delete: bool = True
    ) -> bool:
        """
        Eliminar un registro
        soft_delete=True: Solo marca como inactivo (recomendado)
        soft_delete=False: Elimina físicamente de la BD
        """
        try:
            db_obj = self.get_by_id(db, id, only_active=False)
            if not db_obj:
                return False
            
            if soft_delete:
                db_obj.is_active = False
                db.commit()
            else:
                db.delete(db_obj)
                db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__} {id}: {str(e)}")
            raise DatabaseException(f"Error al eliminar registro")
    
    # ==================== OPERACIONES AVANZADAS ====================
    
    def get_by_field(
        self, 
        db: Session, 
        field_name: str, 
        field_value: Any,
        only_active: bool = True
    ) -> Optional[ModelType]:
        """Obtener un registro por cualquier campo"""
        try:
            if not hasattr(self.model, field_name):
                raise ValueError(f"Field {field_name} does not exist in {self.model.__name__}")
            
            query = db.query(self.model).filter(getattr(self.model, field_name) == field_value)
            if only_active:
                query = query.filter(self.model.is_active == True)
            return query.first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by {field_name}: {str(e)}")
            raise DatabaseException(f"Error al buscar registro")
    
    def get_all_by_field(
        self, 
        db: Session, 
        field_name: str, 
        field_value: Any,
        only_active: bool = True
    ) -> List[ModelType]:
        """Obtener todos los registros que coincidan con un campo"""
        try:
            if not hasattr(self.model, field_name):
                raise ValueError(f"Field {field_name} does not exist in {self.model.__name__}")
            
            query = db.query(self.model).filter(getattr(self.model, field_name) == field_value)
            if only_active:
                query = query.filter(self.model.is_active == True)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__} by {field_name}: {str(e)}")
            raise DatabaseException(f"Error al buscar registros")
    
    def exists(self, db: Session, field_name: str, field_value: Any) -> bool:
        """Verificar si existe un registro con un campo específico"""
        try:
            if not hasattr(self.model, field_name):
                return False
            return db.query(self.model).filter(
                getattr(self.model, field_name) == field_value
            ).first() is not None
        except Exception as e:
            logger.error(f"Error checking existence in {self.model.__name__}: {str(e)}")
            return False
    
    def count(self, db: Session, only_active: bool = True) -> int:
        """Contar registros"""
        try:
            query = db.query(func.count(self.model.id))
            if only_active:
                query = query.filter(self.model.is_active == True)
            return query.scalar()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            return 0
    
    def search(
        self,
        db: Session,
        filters: Dict[str, Any] = None,
        order_by: str = "id",
        order_dir: str = "asc",
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True
    ) -> List[ModelType]:
        """Búsqueda avanzada con filtros dinámicos y ordenamiento"""
        try:
            query = db.query(self.model)
            
            # Aplicar filtro de activos
            if only_active:
                query = query.filter(self.model.is_active == True)
            
            # Aplicar filtros dinámicos
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field) and value is not None:
                        query = query.filter(getattr(self.model, field) == value)
            
            # Aplicar ordenamiento
            if hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                query = query.order_by(
                    desc(order_column) if order_dir.lower() == "desc" else asc(order_column)
                )
            
            # Paginación
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error searching {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Error al buscar registros")
    
    def bulk_create(self, db: Session, objects_data: List[Dict[str, Any]]) -> List[ModelType]:
        """Crear múltiples registros de una vez"""
        try:
            db_objects = [self.model(**obj_data) for obj_data in objects_data]
            db.add_all(db_objects)
            db.commit()
            for obj in db_objects:
                db.refresh(obj)
            return db_objects
        except Exception as e:
            db.rollback()
            logger.error(f"Error bulk creating {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Error al crear registros en lote")
    
    def bulk_update(
        self, 
        db: Session, 
        updates: List[Dict[str, Any]]
    ) -> bool:
        """Actualizar múltiples registros (cada dict debe tener 'id')"""
        try:
            for update_data in updates:
                if 'id' not in update_data:
                    continue
                obj_id = update_data.pop('id')
                self.update(db, obj_id, update_data)
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error bulk updating {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"Error al actualizar registros en lote")