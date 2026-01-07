import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.athlete_schema import (
    AthleteDetailResponse,
    AthleteFilter,
    AthleteInscriptionDTO,
    AthleteInscriptionResponseDTO,
    AthleteUpdateDTO,
    AthleteUpdateResponse,
    MinorAthleteInscriptionDTO,
    MinorAthleteInscriptionResponseDTO,
)
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.utils.exceptions import AppException
from app.utils.security import get_current_account

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/athletes", tags=["Athletes"])
athlete_controller = AthleteController()


# ==========================================
# ENDPOINTS PÚBLICOS


@router.post(
    "/register-minor",
    response_model=ResponseSchema[MinorAthleteInscriptionResponseDTO],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar deportista menor de edad",
    description="Inscribe un deportista menor de edad junto con su representante. "
    "Endpoint público para auto-registro. Si el representante ya existe (por DNI), "
    "se reutiliza automáticamente.",
)
async def register_minor_athlete(
    payload: MinorAthleteInscriptionDTO,
    db: Annotated[Session, Depends(get_db)],
) -> ResponseSchema[MinorAthleteInscriptionResponseDTO]:
    """
    Registra un deportista menor de edad con su representante.

    - Si el representante ya existe (por DNI), se reutiliza.
    - Si no existe, se crea nuevo representante.
    - Crea el atleta menor con la referencia al representante.
    - Crea estadísticas iniciales para el atleta.
    """
    try:
        result = await athlete_controller.register_minor_athlete(db=db, data=payload)
        return ResponseSchema(
            status="success",
            message="Deportista menor registrado exitosamente",
            data=result.model_dump(),
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Error inesperado: {str(exc)}"
        ) from exc


@router.post(
    "/register-unl",
    response_model=ResponseSchema[AthleteInscriptionResponseDTO],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar deportista UNL",
    description="Inscribe un nuevo deportista de la Universidad Nacional de Loja",
)
async def register_athlete_unl(
    payload: AthleteInscriptionDTO,
    db: Annotated[Session, Depends(get_db)],
) -> ResponseSchema[AthleteInscriptionResponseDTO]:
    """Registra un deportista de la UNL en el sistema."""
    try:
        result = await athlete_controller.register_athlete_unl(db=db, data=payload)
        return ResponseSchema(
            status="success",
            message="Deportista registrado exitosamente. Se han generado sus estadísticas iniciales.",
            data=result.model_dump(),
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500, detail=f"Error inesperado: {str(exc)}"
        ) from exc


# ==========================================
# ENDPOINTS CON AUTENTICACIÓN


@router.get(
    "/all",
    response_model=ResponseSchema[PaginatedResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener todos los atletas con paginación",
    description=(
        "Obtiene una lista paginada de todos los atletas, "
        "con opción de búsqueda y filtrado. Requiere autenticación."
    ),
)
def get_all_athletes(
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[AthleteFilter, Depends()],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene todos los atletas con filtros y paginación."""
    try:
        result = athlete_controller.get_all_athletes(db=db, filters=filters)
        
        # Generar mensaje contextual según filtros aplicados
        message = ""
        if filters.search:
            message = f"Resultados de búsqueda: Se muestran los atletas que coinciden con '{filters.search}'."
        elif filters.gender:
            gender_label = "masculino" if filters.gender.lower() == "m" else "femenino"
            message = f"Filtro aplicado: Mostrando únicamente atletas de género {gender_label}."
        elif filters.is_active is not None:
            message = "Vista actualizada: Mostrando solo los deportistas que se encuentran activos actualmente." if filters.is_active else "Vista actualizada: Mostrando deportistas inactivos."
        elif filters.athlete_type:
            message = "Filtro por categoría: Mostrando deportistas pertenecientes al estamento UNL." if filters.athlete_type.upper() == "UNL" else f"Filtro por categoría: Mostrando deportistas de tipo {filters.athlete_type}."
        else:
            page_size = filters.page_size or 10
            message = f"Lista de atletas cargada exitosamente. Mostrando {page_size} registros por página."
        
        return ResponseSchema(
            status="success",
            message=message,
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
    "/{athlete_id}",
    response_model=ResponseSchema[AthleteDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener atleta por ID",
    description="Obtiene los detalles completos de un atleta por su ID con información"
    "local y del MS de usuarios. Requiere autenticación.",
)
async def get_by_id(
    athlete_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene un atleta por su ID con toda la información disponible."""
    try:
        result = await athlete_controller.get_athlete_with_ms_info(
            db=db, athlete_id=athlete_id
        )
        if not result:
            return JSONResponse(
                status_code=404,
                content=ResponseSchema(
                    status="error",
                    message="Deportista no encontrado: El registro solicitado no existe o no está disponible en este club.",
                    data=None,
                    errors=None,
                ).model_dump(),
            )
        return ResponseSchema(
            status="success",
            message="Información recuperada: Los datos del deportista se han cargado correctamente.",
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
    "/update/{athlete_id}",
    response_model=ResponseSchema[AthleteUpdateResponse],
    status_code=status.HTTP_200_OK,
    summary="Actualizar atleta",
    description="Actualiza los datos básicos de un atleta. Requiere autenticación.",
)
async def update_athlete(
    athlete_id: int,
    payload: AthleteUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Actualiza los datos básicos de un atleta."""
    try:
        update_data = payload.model_dump(exclude_unset=True)
        result = await athlete_controller.update_athlete(
            db=db, athlete_id=athlete_id, update_data=update_data
        )
        if not result:
            return JSONResponse(
                status_code=404,
                content=ResponseSchema(
                    status="error",
                    message="No se pudo completar la acción: El deportista que intenta editar no se encuentra registrado.",
                    data=None,
                    errors=None,
                ).model_dump(),
            )
        return ResponseSchema(
            status="success",
            message="Actualización exitosa: El peso y la altura del deportista han sido registrados correctamente.",
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


@router.patch(
    "/desactivate/{athlete_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Desactivar atleta",
    description="Desactiva un atleta (soft delete). Requiere autenticación.",
)
def desactivate_athlete(
    athlete_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Desactiva un atleta (soft delete)."""
    try:
        athlete_controller.desactivate_athlete(db=db, athlete_id=athlete_id)
        return ResponseSchema(
            status="success",
            message="Atleta desactivado: El deportista ya no aparecerá en las listas de entrenamiento activo.",
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
    "/activate/{athlete_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Activar atleta",
    description="Activa un atleta (revierte soft delete). Requiere autenticación.",
)
def activate_athlete(
    athlete_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Activa un atleta (soft undelete)."""
    try:
        athlete_controller.activate_athlete(db=db, athlete_id=athlete_id)
        return ResponseSchema(
            status="success",
            message="Atleta reactivado: El deportista se ha habilitado nuevamente para todas las actividades del club.",
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
