from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.user_controller import UserController
from app.core.database import get_db
from app.models.account import Account
from app.models.enums.rol import Role
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.schemas.user_schema import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    InternFilter,
    InternResponse,
    PromoteAthleteRequest,
    UserDetailResponse,
    UserFilter,
    UserResponse,
)
from app.utils.exceptions import AppException
from app.utils.security import get_current_account, get_current_admin


def get_current_coach_or_admin(
    current_account: Annotated[Account, Depends(get_current_account)],
):
    """Dependencia que valida que el usuario sea Coach o Admin."""
    if current_account.role not in [Role.COACH, Role.ADMINISTRATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo entrenadores o administradores pueden realizar esta acción",
        )
    return current_account


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
        # Incluir el mensaje de error en errors para que el frontend lo muestre
        errors = {"__root__": [exc.message]} if exc.status_code == 422 else None
        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseSchema(
                status="error",
                message=exc.message,
                data=None,
                errors=errors,
            ).model_dump(),
        )
    except Exception as exc:  # pragma: no cover - se devuelve 500 genérico
        return JSONResponse(
            status_code=500,
            content=ResponseSchema(
                status="error",
                message=f"Error inesperado: {str(exc)}",
                data=None,
                errors=None,
            ).model_dump(),
        )


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
    user_id: Annotated[int, Path(gt=0, description="ID del usuario a actualizar")],
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
    "/interns",
    response_model=ResponseSchema[PaginatedResponse[InternResponse]],
    status_code=status.HTTP_200_OK,
    summary="Obtener todos los pasantes",
    description="Lista todos los pasantes con paginación y búsqueda.",
)
def get_all_interns(
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[InternFilter, Depends()],
    current_user: Annotated[Account, Depends(get_current_coach_or_admin)],
):
    """Obtiene todos los pasantes del club."""
    try:
        items, total = user_controller.get_all_interns(db=db, filters=filters)

        return ResponseSchema(
            status="success",
            message="Pasantes obtenidos correctamente",
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
    description="Obtiene los detalles de un usuario por su ID. Requiere autenticación.",
)
async def get_by_id(
    user_id: Annotated[int, Path(gt=0, description="ID del usuario")],
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
    user_id: Annotated[int, Path(gt=0, description="ID del usuario a desactivar")],
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
    user_id: Annotated[int, Path(gt=0, description="ID del usuario a activar")],
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


# ==========================================
# ENDPOINTS DE PASANTES (INTERNS)
# ==========================================


@router.post(
    "/promote-athlete/{athlete_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Promover atleta a pasante",
    description="Crea una cuenta de pasante para un atleta existente.",
)
async def promote_athlete_to_intern(
    athlete_id: Annotated[int, Path(gt=0, description="ID del atleta a promover")],
    payload: PromoteAthleteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_coach_or_admin)],
) -> ResponseSchema:
    """Promueve un atleta existente a pasante."""
    try:
        result = user_controller.promote_athlete_to_intern(
            db=db,
            athlete_id=athlete_id,
            payload=payload,
        )
        return ResponseSchema(
            status="success",
            message="Atleta promovido a pasante correctamente",
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
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content=ResponseSchema(
                status="error",
                message=f"Error inesperado: {str(exc)}",
                data=None,
                errors=None,
            ).model_dump(),
        )


@router.patch(
    "/interns/{intern_id}/deactivate",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Desactivar pasante",
    description="Desactiva un pasante. Solo Coach o Admin.",
)
async def deactivate_intern(
    intern_id: Annotated[int, Path(gt=0, description="ID del pasante a desactivar")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_coach_or_admin)],
):
    """Desactiva un pasante (soft delete)."""
    try:
        user_controller.deactivate_intern(db=db, account_id=intern_id)
        return ResponseSchema(
            status="success",
            message="Pasante desactivado correctamente",
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
    "/interns/{intern_id}/activate",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Activar pasante",
    description="Activa un pasante. Solo Coach o Admin.",
)
async def activate_intern(
    intern_id: Annotated[int, Path(gt=0, description="ID del pasante a activar")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_coach_or_admin)],
):
    """Activa un pasante."""
    try:
        user_controller.activate_intern(db=db, account_id=intern_id)
        return ResponseSchema(
            status="success",
            message="Pasante activado correctamente",
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
