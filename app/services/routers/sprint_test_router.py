"""Router para endpoints de Sprint Tests."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.sprint_test_controller import SprintTestController
from app.controllers.test_controller import TestController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.response import ResponseSchema
from app.schemas.sprint_test_schema import (
    CreateSprintTestSchema,
    SprintTestResponseSchema,
)
from app.utils.exceptions import DatabaseException
from app.utils.security import get_current_account

router = APIRouter(prefix="/sprint-tests", tags=["Sprint Tests"])
sprint_test_controller = SprintTestController()
test_controller = TestController()


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
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar Sprint Tests",
    description="Obtiene lista de Sprint Tests con paginación.",
)
async def list_sprint_tests(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> ResponseSchema:
    """Listar todos los Sprint Tests."""
    try:
        from app.dao.test_dao import TestDAO

        dao = TestDAO()
        tests = dao.list_tests(db, skip, limit, test_type="sprint_test")

        return ResponseSchema(
            status="success",
            message="Sprint Tests obtenidos correctamente",
            data=[SprintTestResponseSchema.model_validate(t) for t in tests],
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
        deleted = test_controller.delete_test(db, test_id)

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
