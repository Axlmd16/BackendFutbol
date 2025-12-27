from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.user_controller import UserController
from app.core.database import get_db
from app.models.enums.rol import Role
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
    description=(
        "Crea un usuario administrador o entrenador en el club y en el sistema "
        "institucional."
    ),
)
async def admin_create_user(
    payload: AdminCreateUserRequest,
    db: Session = Depends(get_db),  # noqa: B008 (FastAPI dependency pattern)
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
    summary="Obtener todos los usuarios",
    description="Lista paginada de usuarios con filtros opcionales",
)
async def get_all_users(
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
    role: Role | None = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> ResponseSchema:
    filters = UserFilter(page=page, limit=limit, search=search, role=role)

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
    "/{user_id}",
    response_model=ResponseSchema[UserDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener usuario por ID",
    description="Obtiene un usuario específico por su ID",
)
async def get_user_by_id(
    user_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
) -> ResponseSchema:
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
    description="Desactiva un usuario (soft delete)",
)
async def desactivate_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
) -> ResponseSchema:
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
