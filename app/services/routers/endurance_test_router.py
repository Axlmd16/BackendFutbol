"""Router para endpoints de Endurance Tests."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.endurance_test_controller import EnduranceTestController
from app.controllers.test_controller import TestController
from app.core.database import get_db
from app.models.account import Account
from app.models.endurance_test import EnduranceTest
from app.schemas.endurance_test_schema import (
    CreateEnduranceTestSchema,
    EnduranceTestResponseSchema,
    UpdateEnduranceTestSchema,
)
from app.schemas.response import ResponseSchema
from app.utils.exceptions import DatabaseException
from app.utils.security import get_current_account

router = APIRouter(prefix="/endurance-tests", tags=["Endurance Tests"])
endurance_test_controller = EnduranceTestController()
test_controller = TestController()


@router.post(
    "/",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Endurance Test",
    description="Crea un nuevo Endurance Test (prueba de resistencia).",
)
async def create_endurance_test(
    payload: CreateEnduranceTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Crear un nuevo Endurance Test."""
    try:
        test = endurance_test_controller.add_test(
            db=db,
            evaluation_id=payload.evaluation_id,
            athlete_id=payload.athlete_id,
            date=payload.date,
            min_duration=payload.min_duration,
            total_distance_m=payload.total_distance_m,
            observations=payload.observations,
        )

        return ResponseSchema(
            status="success",
            message="Endurance Test creado correctamente",
            data=EnduranceTestResponseSchema.model_validate(test),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar Endurance Tests",
    description="Obtiene lista de Endurance Tests con paginación. Opcionalmente filtrada por evaluación.",  # noqa: E501
)
async def list_endurance_tests(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    evaluation_id: int = Query(
        None, description="Filtrar por evaluation_id (opcional)"
    ),
) -> ResponseSchema:
    """Listar todos los Endurance Tests."""
    try:
        if evaluation_id:
            # Filtrar por evaluación y tipo específico de test
            tests = (
                db.query(EnduranceTest)
                .filter(EnduranceTest.evaluation_id == evaluation_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        else:
            tests = (
                db.query(EnduranceTest)
                .filter(EnduranceTest.is_active)
                .offset(skip)
                .limit(limit)
                .all()
            )  # noqa: E501

        return ResponseSchema(
            status="success",
            message="Endurance Tests obtenidos correctamente",
            data=[EnduranceTestResponseSchema.model_validate(t) for t in tests],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener Endurance Test",
    description="Obtiene detalles de un Endurance Test específico.",
)
async def get_endurance_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Obtener un Endurance Test por ID."""
    try:
        from app.dao.test_dao import TestDAO

        dao = TestDAO()
        test = dao.get_test(db, test_id)

        if not test or test.type != "endurance_test":
            raise HTTPException(status_code=404, detail="Endurance Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Endurance Test obtenido correctamente",
            data=EnduranceTestResponseSchema.model_validate(test),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch(
    "/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar Endurance Test",
    description="Actualiza los datos de un Endurance Test existente.",
)
async def update_endurance_test(
    test_id: int,
    payload: UpdateEnduranceTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Actualizar un Endurance Test."""
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    try:
        updated = endurance_test_controller.update_test(db=db, test_id=test_id, **data)

        if not updated:
            raise HTTPException(status_code=404, detail="Endurance Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Endurance Test actualizado correctamente",
            data=EnduranceTestResponseSchema.model_validate(updated),
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
    summary="Eliminar Endurance Test",
    description="Elimina un Endurance Test.",
)
async def delete_endurance_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Eliminar un Endurance Test."""
    try:
        deleted = test_controller.delete_test(db, test_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Endurance Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Endurance Test eliminado correctamente",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
