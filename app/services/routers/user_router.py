from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.user_controller import UserController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.schemas.user_schema import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    UserDetailResponse,
    UserFilter,
    UserResponse,
)
from app.utils.exceptions import AppException
from app.utils.security import get_current_account, get_current_admin

router = APIRouter(prefix="/users", tags=["Users"])
user_controller = UserController()


@router.post(
    "/create",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario administrador/entrenador",
    description="Crea un usuario administrador o entrenador. Solo admin.",
)
async def admin_create_user(
    payload: AdminCreateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Account, Depends(get_current_admin)],
) -> ResponseSchema:
    """Solo el administrador puede crear usuarios administradores o entrenadores."""

    try:
        result = await user_controller.admin_create_user(
            db=db,
            payload=payload,
        )
        return ResponseSchema(
            status="success",
            message=(
                "Usuario creado correctamente en el club y en el sistema institucional"
            ),
            data=result.model_dump(),
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # pragma: no cover - se devuelve 500 genérico
        raise HTTPException(
            status_code=500, detail=f"Error inesperado: {str(exc)}"
        ) from exc


@router.put(
    "/update/{user_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar usuario administrador/entrenador",
    description="Actualiza un usuario administrador o entrenador. Solo admin.",
)
async def admin_update_user(
    payload: AdminUpdateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    user_id: int,
    current_admin: Annotated[Account, Depends(get_current_admin)],
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
    except Exception as e:  # pragma: no cover - se devuelve 500 genérico
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
        "con opción de búsqueda y filtrado por rol. Requiere autenticación."
    ),
)
def get_all_users(
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[UserFilter, Depends()],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    items, total = user_controller.get_all_users(db=db, filters=filters)

    try:
        items, total = user_controller.get_all_users(db=db, filters=filters)

        return ResponseSchema(
            status="success",
            message="Usuarios obtenidos correctamente",
            data=PaginatedResponse(
                items=items,
                total=total,
                page=filters.page,
                limit=filters.limit,
            ).model_dump(),
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
    "/me",
    response_model=ResponseSchema[UserDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil del usuario actual",
    description="Obtiene los detalles del usuario actualmente autenticado.",
)
async def get_me(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene los detalles del usuario logueado actualmente"""
    try:
        # El ID del usuario está vinculado al ID de la cuenta
        user = await user_controller.get_user_by_id(db=db, user_id=current_user.id)

        if user is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ResponseSchema(
                    status="error",
                    message="Usuario no encontrado",
                    data=None,
                    errors=None,
                ).model_dump(),
            )

        return ResponseSchema(
            status="success",
            message="Perfil obtenido correctamente",
            data=user.model_dump(),
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
    "/{user_id}",
    response_model=ResponseSchema[UserDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener usuario por ID",
    description="Obtiene los detalles de un usuario por su ID. Requiere autenticación.",
)
async def get_by_id(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    try:
        user = await user_controller.get_user_by_id(db=db, user_id=user_id)

        if user is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ResponseSchema(
                    status="error",
                    message="Usuario no encontrado",
                    data=None,
                    errors=None,
                ).model_dump(),
            )

        return ResponseSchema(
            status="success",
            message="Usuario obtenido correctamente",
            data=user.model_dump(),
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


@router.patch(
    "/desactivate/{user_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Desactivar usuario",
    description="Desactiva un usuario. Solo Administradores.",
)
async def desactivate_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Account, Depends(get_current_admin)],
):
    """Desactiva un usuario (soft delete)"""
    try:
        user_controller.desactivate_user(db=db, user_id=user_id)
        return ResponseSchema(
            status="success",
            message="Usuario desactivado correctamente",
            data=None,
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


@router.patch(
    "/activate/{user_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Activar usuario",
    description="Activa un usuario. Solo Administradores.",
)
async def activate_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Account, Depends(get_current_admin)],
):
    """Activa un usuario (soft delete)"""
    try:
        user_controller.activate_user(db=db, user_id=user_id)
        return ResponseSchema(
            status="success",
            message="Usuario activado correctamente",
            data=None,
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
