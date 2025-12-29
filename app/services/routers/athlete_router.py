import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.athlete_schema import (
    AthleteFilter,
    AthleteInscriptionDTO,
    AthleteInscriptionResponseDTO,
    AthleteUpdateDTO,
)
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.utils.exceptions import AppException
from app.utils.security import get_current_account

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/athletes", tags=["Athletes"])
athlete_controller = AthleteController()


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
            message="Deportista registrado exitosamente",
            data=result,
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500, detail=f"Error inesperado: {str(exc)}"
        ) from exc


@router.get(
    "/all",
    response_model=ResponseSchema,
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
        items, total = athlete_controller.get_all_athletes(db=db, filters=filters)

        # Convertir items a dicts simples para respuesta
        athlete_responses = [
            {
                "id": athlete.id,
                "full_name": athlete.full_name,
                "dni": athlete.dni,
                "type_athlete": athlete.type_athlete,
                "sex": getattr(athlete.sex, "value", str(athlete.sex)),
                "is_active": athlete.is_active,
                "height": getattr(athlete, "height", None),
                "weight": getattr(athlete, "weight", None),
                "created_at": getattr(athlete, "created_at", None).isoformat() if getattr(athlete, "created_at", None) else None,
                "updated_at": getattr(athlete, "updated_at", None).isoformat() if getattr(athlete, "updated_at", None) else None,
            }
            for athlete in items
        ]

        return ResponseSchema(
            status="success",
            message="Atletas obtenidos correctamente",
            data=PaginatedResponse(
                items=athlete_responses,
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
    "/{athlete_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener atleta por ID",
    description="Obtiene los detalles completos de un atleta por su ID con información local y del MS de usuarios. Requiere autenticación.",
)
async def get_by_id(
    athlete_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene un atleta por su ID con toda la información disponible."""
    try:
        athlete = athlete_controller.get_athlete_by_id(db=db, athlete_id=athlete_id)

        # Datos locales del atleta
        athlete_response = {
            "id": athlete.id,
            "external_person_id": athlete.external_person_id,
            "full_name": athlete.full_name,
            "dni": athlete.dni,
            "type_athlete": athlete.type_athlete,
            "date_of_birth": (
                athlete.date_of_birth.isoformat() if athlete.date_of_birth else None
            ),
            "height": athlete.height,
            "weight": athlete.weight,
            "sex": getattr(athlete.sex, "value", str(athlete.sex)),
            "is_active": athlete.is_active,
            "created_at": athlete.created_at.isoformat(),
            "updated_at": (
                athlete.updated_at.isoformat() if athlete.updated_at else None
            ),
            # Información del MS de usuarios (puede ser None si no está disponible)
            "ms_person_data": None,
        }

        # Intentar obtener información del MS de usuarios
        try:
            from app.client.person_ms_service import PersonMSService
            person_ms_service = PersonMSService()
            person_data = await person_ms_service.get_user_by_identification(athlete.dni)
            if person_data:
                athlete_response["ms_person_data"] = person_data
        except Exception as ms_error:
            # Si el MS no está disponible, continuar sin esa información
            logger.warning(f"No se pudo obtener información del MS para atleta {athlete_id}: {ms_error}")

        return ResponseSchema(
            status="success",
            message="Atleta obtenido correctamente",
            data=athlete_response,
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
    response_model=ResponseSchema,
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

        updated_athlete = await athlete_controller.update_athlete(
            db=db, athlete_id=athlete_id, update_data=update_data
        )

        return ResponseSchema(
            status="success",
            message="Atleta actualizado correctamente",
            data={
                "id": updated_athlete.id,
                "full_name": updated_athlete.full_name,
                "height": updated_athlete.height,
                "weight": updated_athlete.weight,
                "updated_at": (
                    updated_athlete.updated_at.isoformat()
                    if updated_athlete.updated_at
                    else None
                ),
            },
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
            message="Atleta desactivado correctamente",
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
            message="Atleta activado correctamente",
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
