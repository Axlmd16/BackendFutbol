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
from app.schemas.statistic_schema import UpdateSportsStatsRequest
from app.services.routers.constants import (
    handle_app_exception,
    handle_unexpected_exception,
)
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
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)


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
    start_date: Annotated[Optional[date], Query(description="Fecha de inicio")] = None,
    end_date: Annotated[Optional[date], Query(description="Fecha de fin")] = None,
    type_athlete: Annotated[
        Optional[str], Query(description="Filtro por tipo de atleta")
    ] = None,
    sex: Annotated[Optional[str], Query(description="Filtro por sexo")] = None,
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
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)


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
    start_date: Annotated[Optional[date], Query(description="Fecha de inicio")] = None,
    end_date: Annotated[Optional[date], Query(description="Fecha de fin")] = None,
    type_athlete: Annotated[
        Optional[str], Query(description="Filtro por tipo de atleta")
    ] = None,
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
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)


@router.get(
    "/athlete/{athlete_id}",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener estadísticas individuales de un atleta",
    description=(
        "Obtiene las estadísticas individuales de un atleta incluyendo "
        "rendimiento físico, estadísticas de juego, asistencia y tests."
    ),
)
def get_athlete_individual_stats(
    athlete_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene estadísticas individuales de un atleta."""
    try:
        data = statistic_controller.get_athlete_individual_stats(
            db=db,
            athlete_id=athlete_id,
        )

        if data is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ResponseSchema(
                    status="error",
                    message="Atleta no encontrado",
                    data=None,
                    errors=None,
                ).model_dump(),
            )

        return ResponseSchema(
            status="success",
            message="Estadísticas del atleta obtenidas correctamente",
            data=data,
        )
    except AppException as exc:
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)


@router.patch(
    "/athlete/{athlete_id}/sports-stats",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar estadísticas deportivas de un atleta",
    description=(
        "Actualiza las estadísticas de rendimiento deportivo (partidos, goles, "
        "asistencias, tarjetas) de un atleta específico. Solo Coach o Admin."
    ),
)
def update_sports_stats(
    athlete_id: int,
    payload: "UpdateSportsStatsRequest",
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Actualiza estadísticas deportivas de un atleta."""

    try:
        data = statistic_controller.update_sports_stats(
            db=db,
            athlete_id=athlete_id,
            payload=payload,
        )

        if data is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ResponseSchema(
                    status="error",
                    message="Atleta o estadísticas no encontradas",
                    data=None,
                    errors=None,
                ).model_dump(),
            )

        return ResponseSchema(
            status="success",
            message="Estadísticas deportivas actualizadas correctamente",
            data=data,
        )
    except AppException as exc:
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)
