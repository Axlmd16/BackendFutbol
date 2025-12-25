from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.user_controller import UserController
from app.core.database import get_db
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.schemas.user_schema import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    UserFilter,
    UserResponse,
)
from app.utils.exceptions import AppException

router = APIRouter(prefix="/users", tags=["Users"])
user_controller = UserController()


@router.post(
    "/create",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario administrador/entrenador",
    description="Crea un usuario administrador o entrenador ",
)
async def admin_create_user(
    payload: AdminCreateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    # TODO: agregar dependencia de autenticación
) -> ResponseSchema:
    """Solo el administrador puede crear usuarios administradores o entrenadores"""
    try:
        result = await user_controller.admin_create_user(
            db=db,
            payload=payload,
        )
        return ResponseSchema(
            status="success",
            message="Usuario creado correctamente como administrador/entrenador.",
            data=result.model_dump(),
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error inesperado: {str(e)}"
        ) from e


@router.put(
    "/update",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar usuario administrador/entrenador",
    description="Actualiza un usuario administrador o entrenador ",
)
async def admin_update_user(
    payload: AdminUpdateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    # TODO: agregar dependencia de autenticación
) -> ResponseSchema:
    """Solo el administrador puede actualizar usuarios administradores o entrenadores"""
    try:
        result = await user_controller.admin_update_user(
            db=db,
            payload=payload,
        )
        return ResponseSchema(
            status="success",
            message="Usuario actualizado correctamente",
            data=result.model_dump(),
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error inesperado: {str(e)}"
        ) from e


@router.get(
    "/all",
    response_model=ResponseSchema[PaginatedResponse[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="Obtener todos los usuarios con paginación",
    description=(
        "Obtiene una lista paginada de todos los usuarios, "
        "con opción de búsqueda y filtrado por rol."
    ),
)
def get_all_users(
    db: Annotated[Session, Depends(get_db)], filters: Annotated[UserFilter, Depends()]
):
    items, total = user_controller.get_all_users(db=db, filters=filters)

    return ResponseSchema(
        status="success",
        message="Usuarios obtenidos correctamente",
        data=PaginatedResponse(items=items, total=total),
    )
