"""Router para endpoints de Evaluaciones."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.evaluation_controller import EvaluationController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.evaluation_schema import (
    CreateEvaluationSchema,
    EvaluationFilter,
    EvaluationResponseSchema,
    UpdateEvaluationSchema,
)
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.utils.exceptions import DatabaseException
from app.utils.security import get_current_account

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])
evaluation_controller = EvaluationController()


# ==================== EVALUATION ENDPOINTS ====================


@router.post(
    "/",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una evaluación",
    description="Crea una nueva evaluación. Solo usuarios autenticados.",
)
async def create_evaluation(
    payload: CreateEvaluationSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Crear una nueva evaluación."""
    try:
        evaluation = evaluation_controller.create_evaluation(
            db=db,
            payload=payload,
        )

        return ResponseSchema(
            status="success",
            message="Evaluación creada correctamente",
            data=EvaluationResponseSchema.model_validate(evaluation),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/",
    response_model=ResponseSchema[PaginatedResponse[EvaluationResponseSchema]],
    status_code=status.HTTP_200_OK,
    summary="Listar evaluaciones",
    description="Obtiene lista paginada de evaluaciones con búsqueda y filtros.",
)
async def list_evaluations(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    filters: Annotated[EvaluationFilter, Depends()],
) -> ResponseSchema:
    """Listar todas las evaluaciones con paginación."""
    try:
        items, total = evaluation_controller.list_evaluations_paginated(db, filters)

        return ResponseSchema(
            status="success",
            message="Evaluaciones obtenidas correctamente",
            data=PaginatedResponse(
                items=[EvaluationResponseSchema.model_validate(e) for e in items],
                total=total,
                page=filters.page,
                limit=filters.limit,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/user/{user_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar evaluaciones de un usuario",
    description="Obtiene evaluaciones creadas por un usuario específico.",
)
async def list_user_evaluations(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> ResponseSchema:
    """Listar evaluaciones de un usuario."""
    try:
        evaluations = evaluation_controller.list_evaluations_by_user(
            db, user_id, skip, limit
        )

        return ResponseSchema(
            status="success",
            message="Evaluaciones del usuario obtenidas correctamente",
            data=[EvaluationResponseSchema.model_validate(e) for e in evaluations],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/{evaluation_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener evaluación",
    description="Obtiene detalles de una evaluación con todos sus tests.",
)
async def get_evaluation(
    evaluation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Obtener detalles de una evaluación."""
    try:
        evaluation = evaluation_controller.get_evaluation(db, evaluation_id)

        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        # Convertir evaluación a diccionario manualmente
        eval_data = {
            "id": evaluation.id,
            "name": evaluation.name,
            "date": evaluation.date,
            "time": evaluation.time,
            "location": evaluation.location,
            "observations": evaluation.observations,
            "user_id": evaluation.user_id,
            "created_at": evaluation.created_at,
            "updated_at": evaluation.updated_at,
            "is_active": evaluation.is_active,
            "tests": [],  # Por ahora vacío, puede poblarse con tests si es necesario
        }

        return ResponseSchema(
            status="success",
            message="Evaluación obtenida correctamente",
            data=eval_data,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put(
    "/{evaluation_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar evaluación",
    description="Actualiza una evaluación existente.",
)
async def update_evaluation(
    evaluation_id: int,
    payload: UpdateEvaluationSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Actualizar una evaluación."""
    try:
        evaluation = evaluation_controller.update_evaluation(
            db=db,
            evaluation_id=evaluation_id,
            payload=payload,
        )

        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        return ResponseSchema(
            status="success",
            message="Evaluación actualizada correctamente",
            data=EvaluationResponseSchema.model_validate(evaluation),
        )
    except HTTPException:
        raise
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete(
    "/{evaluation_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Eliminar evaluación",
    description="Elimina (soft delete) una evaluación.",
)
async def delete_evaluation(
    evaluation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Eliminar una evaluación."""
    try:
        deleted = evaluation_controller.delete_evaluation(db, evaluation_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        return ResponseSchema(
            status="success",
            message="Evaluación eliminada correctamente",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
