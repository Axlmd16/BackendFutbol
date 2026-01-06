"""Router para endpoints de Sprint Tests."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.sprint_test_controller import SprintTestController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.schemas.sprint_test_schema import (
    CreateSprintTestSchema,
    SprintTestFilter,
    SprintTestResponseSchema,
    UpdateSprintTestSchema,
)
from app.utils.exceptions import DatabaseException
from app.utils.security import get_current_account

router = APIRouter(prefix="/sprint-tests", tags=["Sprint Tests"])
sprint_test_controller = SprintTestController()


@router.post(
    "/",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Sprint Test",
    description="Crea un nuevo Sprint Test (prueba de velocidad).",
)
async def create_sprint_test(
    payload: CreateSprintTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Crear un nuevo Sprint Test."""
    try:
        test = sprint_test_controller.add_test(
            db=db,
            evaluation_id=payload.evaluation_id,
            athlete_id=payload.athlete_id,
            date=payload.date,
            distance_meters=payload.distance_meters,
            time_0_10_s=payload.time_0_10_s,
            time_0_30_s=payload.time_0_30_s,
            observations=payload.observations,
        )

        return ResponseSchema(
            status="success",
            message="Sprint Test creado correctamente",
            data=SprintTestResponseSchema.model_validate(test),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/",
    response_model=ResponseSchema[PaginatedResponse[SprintTestResponseSchema]],
    status_code=status.HTTP_200_OK,
    summary="Listar Sprint Tests",
    description="Obtiene lista paginada de Sprint Tests con filtros.",
)
async def list_sprint_tests(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    filters: Annotated[SprintTestFilter, Depends()],
) -> ResponseSchema:
    """Listar todos los Sprint Tests con paginación."""
    try:
        items, total = sprint_test_controller.list_tests(db, filters)

        return ResponseSchema(
            status="success",
            message="Sprint Tests obtenidos correctamente",
            data=PaginatedResponse(
                items=[SprintTestResponseSchema.model_validate(t) for t in items],
                total=total,
                page=filters.page,
                limit=filters.limit,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener Sprint Test",
    description="Obtiene detalles de un Sprint Test específico.",
)
async def get_sprint_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Obtener un Sprint Test por ID."""
    try:
        from app.dao.test_dao import TestDAO

        dao = TestDAO()
        test = dao.get_test(db, test_id)

        if not test or test.type != "sprint_test":
            raise HTTPException(status_code=404, detail="Sprint Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Sprint Test obtenido correctamente",
            data=SprintTestResponseSchema.model_validate(test),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch(
    "/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar Sprint Test",
    description="Actualiza los datos de un Sprint Test existente.",
)
async def update_sprint_test(
    test_id: int,
    payload: UpdateSprintTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Actualizar un Sprint Test."""
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    try:
        updated = sprint_test_controller.update_test(db=db, test_id=test_id, **data)

        if not updated:
            raise HTTPException(status_code=404, detail="Sprint Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Sprint Test actualizado correctamente",
            data=SprintTestResponseSchema.model_validate(updated),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete(
    "/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Eliminar Sprint Test",
    description="Elimina un Sprint Test.",
)
async def delete_sprint_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Eliminar un Sprint Test."""
    try:
        deleted = sprint_test_controller.delete_test(db, test_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Sprint Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Sprint Test eliminado correctamente",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
