"""Router de representantes - endpoints CRUD."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import Field
from sqlalchemy.orm import Session

from app.controllers.representative_controller import RepresentativeController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.representative_schema import (
    RepresentativeDetailResponse,
    RepresentativeFilter,
    RepresentativeInscriptionDTO,
    RepresentativeInscriptionResponseDTO,
    RepresentativeResponse,
    RepresentativeUpdateDTO,
)
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.services.routers.constants import unexpected_error_message
from app.utils.exceptions import AppException
from app.utils.security import get_current_account, get_current_admin

router = APIRouter(prefix="/representatives", tags=["Representatives"])
representative_controller = RepresentativeController()


# ==========================================
# ENDPOINTS PÚBLICOS


@router.get(
    "/by-dni/{dni}",
    response_model=ResponseSchema[RepresentativeResponse],
    status_code=status.HTTP_200_OK,
    summary="Buscar representante por DNI",
    description="Busca un representante por su DNI. Endpoint público para verificar "
    "si el representante ya existe antes de inscribir un menor.",
)
def get_representative_by_dni(
    dni: str,
    db: Annotated[Session, Depends(get_db)],
):
    """Busca un representante por DNI. Útil para el frontend."""
    try:
        result = representative_controller.get_representative_by_dni(db=db, dni=dni)

        if result is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ResponseSchema(
                    status="error",
                    message="Representante no encontrado",
                    data=None,
                    errors=None,
                ).model_dump(),
            )

        return ResponseSchema(
            status="success",
            message="Representante encontrado",
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
                message=unexpected_error_message(e),
                data=None,
                errors=None,
            ).model_dump(),
        )


# ==========================================
# ENDPOINTS CON AUTENTICACIÓN


@router.post(
    "/create",
    response_model=ResponseSchema[RepresentativeInscriptionResponseDTO],
    status_code=status.HTTP_201_CREATED,
    summary="Crear representante",
    description="Crea un nuevo representante. Solo administradores.",
)
async def create_representative(
    payload: RepresentativeInscriptionDTO,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Account, Depends(get_current_admin)],
):
    """Solo el administrador puede crear representantes directamente."""
    try:
        result = await representative_controller.create_representative(
            db=db, data=payload
        )
        return ResponseSchema(
            status="success",
            message="Representante creado correctamente",
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
                message=unexpected_error_message(e),
                data=None,
                errors=None,
            ).model_dump(),
        )


@router.get(
    "/all",
    response_model=ResponseSchema[PaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener todos los representantes",
    description="Obtiene lista paginada de representantes. Requiere autenticación.",
)
def get_all_representatives(
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[RepresentativeFilter, Depends()],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene todos los representantes con filtros y paginación."""
    try:
        result = representative_controller.get_all_representatives(
            db=db, filters=filters
        )
        return ResponseSchema(
            status="success",
            message="Representantes obtenidos correctamente",
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
                message=unexpected_error_message(e),
                data=None,
                errors=None,
            ).model_dump(),
        )


@router.get(
    "/{representative_id}",
    response_model=ResponseSchema[RepresentativeDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener representante por ID",
    description="Obtiene detalles de un representante incluyendo info del MS.",
)
async def get_representative_by_id(
    representative_id: Annotated[int, Field(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene un representante por su ID con toda la información disponible."""
    try:
        result = await representative_controller.get_representative_by_id(
            db=db, representative_id=representative_id
        )
        return ResponseSchema(
            status="success",
            message="Representante obtenido correctamente",
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
                message=unexpected_error_message(e),
                data=None,
                errors=None,
            ).model_dump(),
        )


@router.put(
    "/update/{representative_id}",
    response_model=ResponseSchema[RepresentativeDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Actualizar representante",
    description="Actualiza los datos de un representante. Solo administradores.",
)
async def update_representative(
    representative_id: Annotated[int, Field(ge=1)],
    payload: RepresentativeUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Account, Depends(get_current_admin)],
):
    """Actualiza un representante."""
    try:
        result = await representative_controller.update_representative(
            db=db, representative_id=representative_id, data=payload
        )
        return ResponseSchema(
            status="success",
            message="Representante actualizado correctamente",
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
                message=unexpected_error_message(e),
                data=None,
                errors=None,
            ).model_dump(),
        )


@router.patch(
    "/deactivate/{representative_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Desactivar representante",
    description="Desactiva un representante (soft delete). Solo administradores.",
)
def deactivate_representative(
    representative_id: Annotated[int, Field(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Account, Depends(get_current_admin)],
):
    """Desactiva un representante (soft delete)."""
    try:
        representative_controller.deactivate_representative(
            db=db, representative_id=representative_id
        )
        return ResponseSchema(
            status="success",
            message="Representante desactivado correctamente",
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
                message=unexpected_error_message(e),
                data=None,
                errors=None,
            ).model_dump(),
        )


@router.patch(
    "/activate/{representative_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Activar representante",
    description="Activa un representante. Solo administradores.",
)
def activate_representative(
    representative_id: Annotated[int, Field(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[Account, Depends(get_current_admin)],
):
    """Activa un representante."""
    try:
        representative_controller.activate_representative(
            db=db, representative_id=representative_id
        )
        return ResponseSchema(
            status="success",
            message="Representante activado correctamente",
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
                message=unexpected_error_message(e),
                data=None,
                errors=None,
            ).model_dump(),
        )
