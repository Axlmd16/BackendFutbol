from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.user_controller import UserController
from app.core.database import get_db
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.schemas.user_schema import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    UserDetailResponse,
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
        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseSchema(
                status="error",
                message=exc.message,
                data=None,
                errors=None,
            ).model_dump(),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ResponseSchema(
                status="error",
                message=f"Error inesperado: {str(e)}",
                data=None,
                errors=None,
            ).model_dump(),
        )


@router.put(
    "/update/{user_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar usuario administrador/entrenador",
    description="Actualiza un usuario administrador o entrenador ",
)
async def admin_update_user(
    payload: AdminUpdateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    user_id: int,
    # TODO: agregar dependencia de autenticación
) -> ResponseSchema:
    """Solo el administrador puede actualizar usuarios administradores o entrenadores"""
    try:
        result = await user_controller.admin_update_user(
            db=db,
            payload=payload,
            user_id=user_id,
        )
        return ResponseSchema(
            status="success",
            message="Usuario actualizado correctamente",
            data=result.model_dump(),
        )
    except AppException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseSchema(
                status="error",
                message=exc.message,
                data=None,
                errors=None,
            ).model_dump(),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ResponseSchema(
                status="error",
                message=f"Error inesperado: {str(e)}",
                data=None,
                errors=None,
            ).model_dump(),
        )


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


@router.get(
    "/{user_id}",
    response_model=ResponseSchema[UserDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener usuario por ID",
    description="Obtiene los detalles de un usuario específico por su ID.",
)
async def get_by_id(user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = await user_controller.get_user_by_id(db=db, user_id=user_id)
    if not user:
        raise AppException(status_code=404, message="Usuario no encontrado")
    return ResponseSchema(
        status="success",
        message="Usuario obtenido correctamente",
        data=user.model_dump(),
    )


@router.patch(
    "/desactivate/{user_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Desactivar usuario",
    description="Desactiva un usuario, impidiendo su acceso al sistema.",
)
def desactivate_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """Desactiva un usuario (soft delete)"""
    user_controller.desactivate_user(db=db, user_id=user_id)
    return ResponseSchema(
        status="success",
        message="Usuario desactivado correctamente",
        data=None,
    )
