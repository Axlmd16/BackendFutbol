from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.controllers.user_controller import UserController
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse, UserLogin
from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException

router = APIRouter(prefix="/users", tags=["Users"])
user_controller = UserController()


def handle_error(e: Exception):
    """Manejador centralizado de errores"""
    if isinstance(e, AppException):
        raise HTTPException(status_code=e.status_code, detail=e.message)
    raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS PÚBLICOS ====================

@router.get("/", response_model=ResponseSchema)
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Listar todos los usuarios (público)"""
    try:
        users = user_controller.get_all_users(db, skip, limit)
        total = user_controller.get_user_count(db)
        
        return ResponseSchema(
            status="success",
            message=f"Se encontraron {len(users)} usuarios de {total}",
            data={
                "users": [UserResponse.model_validate(u) for u in users],
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        handle_error(e)


@router.post("/register", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario (público)"""
    try:
        new_user = user_controller.create_user(db, user_data)
        return ResponseSchema(
            status="success",
            message="Usuario registrado exitosamente",
            data=UserResponse.model_validate(new_user)
        )
    except Exception as e:
        handle_error(e)


@router.post("/login", response_model=ResponseSchema)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login de usuario (público)"""
    try:
        user = user_controller.authenticate_user(db, credentials.email, credentials.password)
        return ResponseSchema(
            status="success",
            message="Login exitoso",
            data={
                "user": UserResponse.model_validate(user),
                "token": "TODO: Implementar JWT"
            }
        )
    except Exception as e:
        handle_error(e)


# ==================== ENDPOINTS PRIVADOS ====================

@router.get("/{user_id}", response_model=ResponseSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Obtener usuario por ID (privado)"""
    # TODO: Agregar Depends(get_current_user)
    try:
        user = user_controller.get_user_by_id(db, user_id)
        return ResponseSchema(
            status="success",
            message="Usuario obtenido",
            data=UserResponse.model_validate(user)
        )
    except Exception as e:
        handle_error(e)


@router.put("/{user_id}", response_model=ResponseSchema)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Actualizar usuario (privado)"""
    # TODO: Agregar Depends(get_current_user)
    try:
        updated = user_controller.update_user(db, user_id, user_data)
        return ResponseSchema(
            status="success",
            message="Usuario actualizado",
            data=UserResponse.model_validate(updated)
        )
    except Exception as e:
        handle_error(e)