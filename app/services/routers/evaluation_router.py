"""Router para endpoints de Evaluaciones."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.evaluation_controller import EvaluationController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.evaluation_schema import (
    CreateEnduranceTestSchema,
    CreateEvaluationSchema,
    CreateSprintTestSchema,
    CreateTechnicalAssessmentSchema,
    CreateYoyoTestSchema,
    EnduranceTestResponseSchema,
    EvaluationDetailSchema,
    EvaluationResponseSchema,
    SprintTestResponseSchema,
    TechnicalAssessmentResponseSchema,
    UpdateEvaluationSchema,
    YoyoTestResponseSchema,
)
from app.schemas.response import ResponseSchema
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
            name=payload.name,
            date=payload.date,
            time=payload.time,
            user_id=payload.user_id,
            location=payload.location,
            observations=payload.observations,
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
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar evaluaciones",
    description="Obtiene lista paginada de evaluaciones.",
)
async def list_evaluations(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> ResponseSchema:
    """Listar todas las evaluaciones."""
    try:
        evaluations = evaluation_controller.list_evaluations(db, skip, limit)

        return ResponseSchema(
            status="success",
            message="Evaluaciones obtenidas correctamente",
            data=[EvaluationResponseSchema.model_validate(e) for e in evaluations],
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

        return ResponseSchema(
            status="success",
            message="Evaluación obtenida correctamente",
            data=EvaluationDetailSchema.model_validate(evaluation),
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
            name=payload.name,
            date=payload.date,
            time=payload.time,
            location=payload.location,
            observations=payload.observations,
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


# ==================== SPRINT TEST ENDPOINTS ====================


@router.post(
    "/{evaluation_id}/sprint-tests",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar Sprint Test",
    description="Crea un Sprint Test (prueba de velocidad) en una evaluación.",
)
async def add_sprint_test(
    evaluation_id: int,
    payload: CreateSprintTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Agregar un Sprint Test a una evaluación."""
    try:
        test = evaluation_controller.add_sprint_test(
            db=db,
            evaluation_id=evaluation_id,
            athlete_id=payload.athlete_id,
            date=payload.date,
            distance_meters=payload.distance_meters,
            time_0_10_s=payload.time_0_10_s,
            time_0_30_s=payload.time_0_30_s,
            observations=payload.observations,
        )

        return ResponseSchema(
            status="success",
            message="Sprint Test agregado correctamente",
            data=SprintTestResponseSchema.model_validate(test),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ==================== YOYO TEST ENDPOINTS ====================


@router.post(
    "/{evaluation_id}/yoyo-tests",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar Yoyo Test",
    description="Crea un Yoyo Test (prueba de resistencia aerobia) en una evaluación.",
)
async def add_yoyo_test(
    evaluation_id: int,
    payload: CreateYoyoTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Agregar un Yoyo Test a una evaluación."""
    try:
        test = evaluation_controller.add_yoyo_test(
            db=db,
            evaluation_id=evaluation_id,
            athlete_id=payload.athlete_id,
            date=payload.date,
            shuttle_count=payload.shuttle_count,
            final_level=payload.final_level,
            failures=payload.failures,
            observations=payload.observations,
        )

        return ResponseSchema(
            status="success",
            message="Yoyo Test agregado correctamente",
            data=YoyoTestResponseSchema.model_validate(test),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ==================== ENDURANCE TEST ENDPOINTS ====================


@router.post(
    "/{evaluation_id}/endurance-tests",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar Endurance Test",
    description="Crea un Endurance Test (prueba de resistencia) en una evaluación.",
)
async def add_endurance_test(
    evaluation_id: int,
    payload: CreateEnduranceTestSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Agregar un Endurance Test a una evaluación."""
    try:
        test = evaluation_controller.add_endurance_test(
            db=db,
            evaluation_id=evaluation_id,
            athlete_id=payload.athlete_id,
            date=payload.date,
            min_duration=payload.min_duration,
            total_distance_m=payload.total_distance_m,
            observations=payload.observations,
        )

        return ResponseSchema(
            status="success",
            message="Endurance Test agregado correctamente",
            data=EnduranceTestResponseSchema.model_validate(test),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ==================== TECHNICAL ASSESSMENT ENDPOINTS ====================


@router.post(
    "/{evaluation_id}/technical-assessments",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar Evaluación Técnica",
    description="Crea una evaluación técnica (Technical Assessment) en una evaluación.",
)
async def add_technical_assessment(
    evaluation_id: int,
    payload: CreateTechnicalAssessmentSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Agregar una evaluación técnica a una evaluación."""
    try:
        test = evaluation_controller.add_technical_assessment(
            db=db,
            evaluation_id=evaluation_id,
            athlete_id=payload.athlete_id,
            date=payload.date,
            ball_control=payload.ball_control,
            short_pass=payload.short_pass,
            long_pass=payload.long_pass,
            shooting=payload.shooting,
            dribbling=payload.dribbling,
            observations=payload.observations,
        )

        return ResponseSchema(
            status="success",
            message="Evaluación técnica agregada correctamente",
            data=TechnicalAssessmentResponseSchema.model_validate(test),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ==================== TEST MANAGEMENT ENDPOINTS ====================


@router.get(
    "/{evaluation_id}/tests",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar tests de una evaluación",
    description="Obtiene todos los tests asociados a una evaluación.",
)
async def list_evaluation_tests(
    evaluation_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Listar tests de una evaluación."""
    try:
        tests = evaluation_controller.list_tests_by_evaluation(db, evaluation_id)

        return ResponseSchema(
            status="success",
            message="Tests de la evaluación obtenidos correctamente",
            data=[
                {
                    "id": test.id,
                    "type": test.type,
                    "date": test.date,
                    "athlete_id": test.athlete_id,
                    "evaluation_id": test.evaluation_id,
                    "observations": test.observations,
                }
                for test in tests
            ],
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete(
    "/tests/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Eliminar test",
    description="Elimina un test de una evaluación.",
)
async def delete_test(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Eliminar un test."""
    try:
        deleted = evaluation_controller.delete_test(db, test_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Test no encontrado")

        return ResponseSchema(
            status="success",
            message="Test eliminado correctamente",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
