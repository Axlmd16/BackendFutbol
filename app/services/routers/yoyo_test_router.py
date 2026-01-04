"""Router para endpoints de Yoyo Tests."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.yoyo_test_controller import YoyoTestController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.schemas.yoyo_test_schema import (
    CreateYoyoTestSchema,
    UpdateYoyoTestSchema,
    YoyoTestFilter,
    YoyoTestResponseSchema,
)
from app.utils.exceptions import DatabaseException
from app.utils.security import get_current_account

router = APIRouter(prefix="/yoyo-tests", tags=["Yoyo Tests"])
yoyo_test_controller = YoyoTestController()


@router.post(
    "/",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Yoyo Test",
    description="Crea un nuevo Yoyo Test (prueba de resistencia aerobia).",
)
async def create_yoyo_test(
    payload: CreateYoyoTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Crear un nuevo Yoyo Test."""
    try:
        test = yoyo_test_controller.add_test(
            db=db,
            evaluation_id=payload.evaluation_id,
            athlete_id=payload.athlete_id,
            date=payload.date,
            shuttle_count=payload.shuttle_count,
            final_level=payload.final_level,
            failures=payload.failures,
            observations=payload.observations,
        )

        return ResponseSchema(
            status="success",
            message="Yoyo Test creado correctamente",
            data=YoyoTestResponseSchema.model_validate(test),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/",
    response_model=ResponseSchema[PaginatedResponse[YoyoTestResponseSchema]],
    status_code=status.HTTP_200_OK,
    summary="Listar Yoyo Tests",
    description="Obtiene lista paginada de Yoyo Tests con filtros.",
)
async def list_yoyo_tests(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    filters: Annotated[YoyoTestFilter, Depends()],
) -> ResponseSchema:
    """Listar todos los Yoyo Tests con paginación."""
    try:
        items, total = yoyo_test_controller.list_tests(db, filters)

        return ResponseSchema(
            status="success",
            message="Yoyo Tests obtenidos correctamente",
            data=PaginatedResponse(
                items=[YoyoTestResponseSchema.model_validate(t) for t in items],
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
    summary="Obtener Yoyo Test",
    description="Obtiene detalles de un Yoyo Test específico.",
)
async def get_yoyo_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Obtener un Yoyo Test por ID."""
    try:
        from app.dao.test_dao import TestDAO

        dao = TestDAO()
        test = dao.get_test(db, test_id)

        if not test or test.type != "yoyo_test":
            raise HTTPException(status_code=404, detail="Yoyo Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Yoyo Test obtenido correctamente",
            data=YoyoTestResponseSchema.model_validate(test),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch(
    "/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar Yoyo Test",
    description="Actualiza los datos de un Yoyo Test existente.",
)
async def update_yoyo_test(
    test_id: int,
    payload: UpdateYoyoTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Actualizar un Yoyo Test."""
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    try:
        updated = yoyo_test_controller.update_test(db=db, test_id=test_id, **data)

        if not updated:
            raise HTTPException(status_code=404, detail="Yoyo Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Yoyo Test actualizado correctamente",
            data=YoyoTestResponseSchema.model_validate(updated),
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
    summary="Eliminar Yoyo Test",
    description="Elimina un Yoyo Test.",
)
async def delete_yoyo_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Eliminar un Yoyo Test."""
    try:
        deleted = yoyo_test_controller.delete_test(db, test_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Yoyo Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Yoyo Test eliminado correctamente",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
