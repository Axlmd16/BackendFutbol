"""Router de reportes deportivos con endpoints específicos."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.controllers.report_controller import ReportController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.report_schema import ReportFilter, ReportType
from app.utils.exceptions import AppException, ValidationException
from app.utils.security import get_current_account

router = APIRouter(prefix="/reports", tags=["Reports"])
report_controller = ReportController()

# Constante para content types
DEFAULT_CONTENT_TYPE = "application/octet-stream"
CONTENT_TYPES = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
}


def validate_report_permissions(
    current_user: Annotated[Account, Depends(get_current_account)],
) -> Account:
    """Valida que el usuario tenga permisos para generar reportes.

    Args:
        current_user: Cuenta del usuario actual

    Returns:
        Account: La cuenta del usuario si tiene permisos

    Raises:
        ValidationException: Si el usuario no tiene permisos
    """
    user_role = current_user.user.role
    role_value = user_role.value if hasattr(user_role, "value") else str(user_role)
    if role_value not in ["Administrator", "Coach"]:
        raise ValidationException("No tiene permisos para generar reportes")
    return current_user


@router.post(
    "/attendance",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Generar reporte de asistencia",
    description=(
        "Genera un reporte formal de asistencia con datos de deportistas, "
        "porcentajes de asistencia y resúmenes. Soporta filtros por tipo de atleta, "
        "sexo y rango de fechas."
    ),
)
def generate_attendance_report(
    filters: ReportFilter,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(validate_report_permissions)],
):
    """
    Genera reporte de asistencia.

    - **format**: Formato del archivo: pdf, xlsx, csv
    - **start_date**: Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Fecha de fin (YYYY-MM-DD)
    - **athlete_type**: Filtro por tipo de deportista
    - **sex**: Filtro por sexo
    """
    try:
        # Forzar tipo de reporte
        filters.report_type = ReportType.ATTENDANCE

        # Generar reporte
        file_content = report_controller.generate_report(
            db=db,
            filters=filters,
            user_name=current_user.user.full_name,
        )

        # Determinar content type
        content_type = CONTENT_TYPES.get(filters.format, DEFAULT_CONTENT_TYPE)

        # Nombre del archivo
        file_name = f"reporte_asistencia.{filters.format}"

        return StreamingResponse(
            file_content,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )

    except ValidationException as e:
        raise AppException(status_code=400, message=str(e)) from e
    except Exception as e:
        raise AppException(
            status_code=500, message=f"Error al generar reporte: {str(e)}"
        ) from e


@router.post(
    "/tests",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Generar reporte de evaluaciones y tests",
    description=(
        "Genera un reporte formal con resultados de tests físicos (sprint, etc.."
        "técnicos). Incluye promedios y resúmenes por tipo de test."
    ),
)
def generate_tests_report(
    filters: ReportFilter,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(validate_report_permissions)],
):
    """
    Genera reporte de evaluaciones y tests.

    - **format**: Formato del archivo: pdf, xlsx, csv
    - **start_date**: Fecha de inicio
    - **end_date**: Fecha de fin
    - **athlete_type**: Filtro por tipo de deportista
    """
    try:
        # Forzar tipo de reporte
        filters.report_type = ReportType.TESTS

        # Generar reporte
        file_content = report_controller.generate_report(
            db=db,
            filters=filters,
            user_name=current_user.user.full_name,
        )

        # Content type
        content_type = CONTENT_TYPES.get(filters.format, DEFAULT_CONTENT_TYPE)

        # Nombre del archivo
        file_name = f"reporte_tests.{filters.format}"

        return StreamingResponse(
            file_content,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )

    except ValidationException as e:
        raise AppException(status_code=400, message=str(e)) from e
    except Exception as e:
        raise AppException(
            status_code=500, message=f"Error al generar reporte: {str(e)}"
        ) from e


@router.post(
    "/statistics",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Generar reporte de estadísticas generales",
    description=(
        "Genera un reporte ejecutivo con estadísticas consolidadas del club: "
        "totales de deportistas, evaluaciones, tests, y resúmenes generales."
    ),
)
def generate_statistics_report(
    filters: ReportFilter,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(validate_report_permissions)],
):
    """
    Genera reporte de estadísticas generales.

    - **format**: Formato del archivo: pdf, xlsx, csv
    - **athlete_type**: Filtro por tipo de deportista
    - **sex**: Filtro por sexo
    """
    try:
        # Forzar tipo de reporte
        filters.report_type = ReportType.STATISTICS

        # Generar reporte
        file_content = report_controller.generate_report(
            db=db,
            filters=filters,
            user_name=current_user.user.full_name,
        )

        # Content type
        content_type = CONTENT_TYPES.get(filters.format, DEFAULT_CONTENT_TYPE)

        # Nombre del archivo
        file_name = f"reporte_estadisticas.{filters.format}"

        return StreamingResponse(
            file_content,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )

    except ValidationException as e:
        raise AppException(status_code=400, message=str(e)) from e
    except Exception as e:
        raise AppException(
            status_code=500, message=f"Error al generar reporte: {str(e)}"
        ) from e
