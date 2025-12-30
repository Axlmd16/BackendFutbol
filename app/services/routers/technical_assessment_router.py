"""Router para endpoints de Technical Assessments."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.technical_assessment_controller import (
    TechnicalAssessmentController,
)
from app.controllers.test_controller import TestController
from app.core.database import get_db
from app.models.account import Account
from app.models.technical_assessment import TechnicalAssessment
from app.schemas.response import ResponseSchema
from app.schemas.technical_assessment_schema import (
    CreateTechnicalAssessmentSchema,
    TechnicalAssessmentResponseSchema,
)
from app.utils.exceptions import DatabaseException
from app.utils.security import get_current_account

router = APIRouter(prefix="/technical-assessments", tags=["Technical Assessments"])
technical_assessment_controller = TechnicalAssessmentController()
test_controller = TestController()


@router.post(
    "/",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Technical Assessment",
    description="Crea una nueva evaluación técnica.",
)
async def create_technical_assessment(
    payload: CreateTechnicalAssessmentSchema,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Crear una nueva Technical Assessment."""
    try:
        test = technical_assessment_controller.add_test(
            db=db,
            evaluation_id=payload.evaluation_id,
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
            message="Technical Assessment creado correctamente",
            data=TechnicalAssessmentResponseSchema.model_validate(test),
        )
    except DatabaseException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Listar Technical Assessments",
    description="Obtiene lista de Technical Assessments con paginación. Opcionalmente filtrada por evaluación.",  # noqa: E501
)
async def list_technical_assessments(
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    evaluation_id: int = Query(
        None, description="Filtrar por evaluation_id (opcional)"
    ),
) -> ResponseSchema:
    """Listar todos los Technical Assessments."""
    try:
        if evaluation_id:
            # Filtrar por evaluación y tipo específico de test
            tests = (
                db.query(TechnicalAssessment)
                .filter(TechnicalAssessment.evaluation_id == evaluation_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        else:
            tests = (
                db.query(TechnicalAssessment)
                .filter(TechnicalAssessment.is_active)
                .offset(skip)
                .limit(limit)
                .all()
            )  # noqa: E501

        return ResponseSchema(
            status="success",
            message="Technical Assessments obtenidos correctamente",
            data=[TechnicalAssessmentResponseSchema.model_validate(t) for t in tests],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener Technical Assessment",
    description="Obtiene detalles de un Technical Assessment específico.",
)
async def get_technical_assessment(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Obtener un Technical Assessment por ID."""
    try:
        from app.dao.test_dao import TestDAO

        dao = TestDAO()
        test = dao.get_test(db, test_id)

        if not test or test.type != "technical_assessment":
            raise HTTPException(
                status_code=404, detail="Technical Assessment no encontrado"
            )

        return ResponseSchema(
            status="success",
            message="Technical Assessment obtenido correctamente",
            data=TechnicalAssessmentResponseSchema.model_validate(test),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete(
    "/{test_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Eliminar Technical Assessment",
    description="Elimina un Technical Assessment.",
)
async def delete_technical_assessment(
    test_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> ResponseSchema:
    """Eliminar un Technical Assessment."""
    try:
        deleted = test_controller.delete_test(db, test_id)

        if not deleted:
            raise HTTPException(
                status_code=404, detail="Technical Assessment no encontrado"
            )

        return ResponseSchema(
            status="success",
            message="Technical Assessment eliminado correctamente",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
