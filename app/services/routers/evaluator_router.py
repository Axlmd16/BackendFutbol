from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.evaluator_controller import EvaluatorController
from app.core.database import get_db
from app.schemas.evaluator_schema import (
    EvaluatorCreate,
    EvaluatorResponse,
    EvaluatorUpdate,
)
from app.schemas.response import ResponseSchema

router = APIRouter(prefix="/evaluators", tags=["Evaluators"])
evaluator_controller = EvaluatorController()


# Listar evaluadores con paginación básica
@router.get("/", response_model=ResponseSchema)
def list_evaluators(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    only_active: bool = Query(True),
    db: Session = Depends(get_db)
):
    evaluators = evaluator_controller.list(
        db, skip=skip, limit=limit, only_active=only_active
    )
    items = [EvaluatorResponse.model_validate(ev) for ev in evaluators]
    return ResponseSchema(
        status="success",
        message="Evaluadores listados correctamente",
        data={
            "items": items,
            "count": len(items),
            "skip": skip,
            "limit": limit,
        },
    )

# Obtener un evaluador por ID
@router.get("/{evaluator_id}", response_model=ResponseSchema)
def get_evaluator(
    evaluator_id: int,
    db: Session = Depends(get_db)
):
    evaluator = evaluator_controller.get(db, evaluator_id)
    if not evaluator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluador no encontrado",
        )

    return ResponseSchema(
        status="success",
        message="Evaluador obtenido correctamente",
        data=EvaluatorResponse.model_validate(evaluator),
    )

# Crear un nuevo evaluador
@router.post("/", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
def create_evaluator(
    payload: EvaluatorCreate,
    db: Session = Depends(get_db)
):
    evaluator = evaluator_controller.create(db, payload.model_dump())
    return ResponseSchema(
        status="success",
        message="Evaluador creado correctamente",
        data=EvaluatorResponse.model_validate(evaluator),
    )

# Actualizar un evaluador existente
@router.put("/{evaluator_id}", response_model=ResponseSchema)
def update_evaluator(
    evaluator_id: int,
    payload: EvaluatorUpdate,
    db: Session = Depends(get_db)
):
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar",
        )

    evaluator = evaluator_controller.update(db, evaluator_id, update_data)
    if not evaluator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluador no encontrado",
        )

    return ResponseSchema(
        status="success",
        message="Evaluador actualizado correctamente",
        data=EvaluatorResponse.model_validate(evaluator),
    )

# Eliminar (o desactivar) un evaluador
@router.delete("/{evaluator_id}", response_model=ResponseSchema)
def delete_evaluator(
    evaluator_id: int,
    soft_delete: bool = Query(True),
    db: Session = Depends(get_db)
):
    deleted = evaluator_controller.delete(
        db, evaluator_id, soft_delete=soft_delete
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluador no encontrado",
        )

    action = "desactivado" if soft_delete else "eliminado"
    return ResponseSchema(
        status="success",
        message=f"Evaluador {action} correctamente",
        data={"id": evaluator_id},
    )
