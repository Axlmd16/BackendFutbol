"""Router de estadísticas con endpoints para métricas del club."""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.statistic_controller import StatisticController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException
from app.utils.security import get_current_account

router = APIRouter(prefix="/statistics", tags=["Statistics"])
statistic_controller = StatisticController()


@router.get(
    "/overview",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener métricas generales del club",
    description=(
        "Obtiene un resumen de las métricas generales del club incluyendo "
        "total de atletas, distribución por tipo y género, y totales de "
        "evaluaciones y tests."
    ),
)
def get_club_overview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
    type_athlete: Optional[str] = Query(None, description="Filtro por tipo de atleta"),
    sex: Optional[str] = Query(None, description="Filtro por sexo (MALE, FEMALE)"),
):
    """Obtiene métricas generales del club."""
    try:
        data = statistic_controller.get_club_overview(
            db=db,
            type_athlete=type_athlete,
            sex=sex,
        )

        return ResponseSchema(
            status="success",
            message="Resumen del club obtenido correctamente",
            data=data,
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
    "/attendance",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener estadísticas de asistencia",
    description=(
        "Obtiene estadísticas detalladas de asistencia incluyendo tasas, "
        "tendencias por período y distribución por tipo de atleta."
    ),
)
def get_attendance_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
    start_date: Optional[date] = Query(None, description="Fecha de inicio"),
    end_date: Optional[date] = Query(None, description="Fecha de fin"),
    type_athlete: Optional[str] = Query(None, description="Filtro por tipo de atleta"),
    sex: Optional[str] = Query(None, description="Filtro por sexo"),
):
    """Obtiene estadísticas de asistencia."""
    try:
        data = statistic_controller.get_attendance_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date,
            type_athlete=type_athlete,
            sex=sex,
        )

        return ResponseSchema(
            status="success",
            message="Estadísticas de asistencia obtenidas correctamente",
            data=data,
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
    "/tests",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener estadísticas de rendimiento en tests",
    description=(
        "Obtiene estadísticas de rendimiento incluyendo totales por tipo de test, "
        "promedios, y top performers."
    ),
)
def get_test_performance(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
    start_date: Optional[date] = Query(None, description="Fecha de inicio"),
    end_date: Optional[date] = Query(None, description="Fecha de fin"),
    type_athlete: Optional[str] = Query(None, description="Filtro por tipo de atleta"),
):
    """Obtiene estadísticas de rendimiento en tests."""
    try:
        data = statistic_controller.get_test_performance(
            db=db,
            start_date=start_date,
            end_date=end_date,
            type_athlete=type_athlete,
        )

        return ResponseSchema(
            status="success",
            message="Estadísticas de tests obtenidas correctamente",
            data=data,
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
