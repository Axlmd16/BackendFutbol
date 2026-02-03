"""Router de asistencias con endpoints para registro en lote y consultas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers.attendance_controller import AttendanceController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.attendance_schema import (
    AttendanceBulkCreate,
    AttendanceBulkResponse,
    AttendanceFilter,
)
from app.schemas.response import PaginatedResponse, ResponseSchema
from app.services.routers.constants import (
    handle_app_exception,
    handle_unexpected_exception,
)
from app.utils.exceptions import AppException
from app.utils.security import get_current_account

router = APIRouter(prefix="/attendances", tags=["Attendances"])
attendance_controller = AttendanceController()


@router.post(
    "/bulk",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar asistencias en lote",
    description=(
        "Crea o actualiza múltiples registros de asistencia para una fecha específica. "
        "Si ya existe un registro para un atleta en esa fecha, se actualiza. "
        "Si no se proporciona hora, se usa la hora actual."
    ),
)
def create_bulk_attendance(
    payload: AttendanceBulkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Crea o actualiza asistencias en lote."""
    try:
        created, updated = attendance_controller.create_bulk_attendance(
            db=db,
            data=payload,
            user_dni=current_user.user.dni,
        )

        return ResponseSchema(
            status="success",
            message="Asistencias procesadas correctamente",
            data=AttendanceBulkResponse(
                created_count=created,
                updated_count=updated,
            ).model_dump(),
        )
    except AppException as exc:
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)


@router.get(
    "/dates",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener fechas con registros",
    description="Obtiene una lista de todas las fechas"
    "que tienen registros de asistencia.",
)
def get_attendance_dates(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene lista de fechas con asistencia."""
    try:
        dates = attendance_controller.get_existing_dates(db)

        return ResponseSchema(
            status="success",
            message="Fechas obtenidas correctamente",
            data=dates,
        )
    except AppException as exc:
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)


@router.get(
    "/by-date",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener asistencias por fecha",
    description=(
        "Obtiene los registros de asistencia para una fecha específica, "
        "con filtros opcionales por tipo de atleta y búsqueda."
    ),
)
def get_attendances_by_date(
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[AttendanceFilter, Depends()],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene asistencias por fecha con filtros."""
    try:
        items, total = attendance_controller.get_attendances_by_date(
            db=db,
            filters=filters,
        )

        return ResponseSchema(
            status="success",
            message="Asistencias obtenidas correctamente",
            data=PaginatedResponse(
                items=items,
                total=total,
                page=filters.page,
                limit=filters.limit,
            ).model_dump(),
        )
    except AppException as exc:
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)


@router.get(
    "/summary",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Obtener resumen de asistencia",
    description="Obtiene un resumen estadístico de asistencia para una fecha.",
)
def get_attendance_summary(
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[AttendanceFilter, Depends()],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """Obtiene resumen de asistencia por fecha."""
    try:
        summary = attendance_controller.get_attendance_summary(
            db=db,
            target_date=filters.attendance_date,
        )

        return ResponseSchema(
            status="success",
            message="Resumen obtenido correctamente",
            data=summary,
        )
    except AppException as exc:
        return handle_app_exception(exc)
    except Exception as e:
        return handle_unexpected_exception(e)
