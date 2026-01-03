"""Router de reportes deportivos con endpoints para generación de reportes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.controllers.report_controller import ReportController
from app.core.database import get_db
from app.models.account import Account
from app.schemas.report_schema import ReportFilter, ReportGenerationResponse
from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException, ValidationException
from app.utils.security import get_current_account
from datetime import date

router = APIRouter(prefix="/reports", tags=["Reports"])
report_controller = ReportController()


@router.post(
    "/generate",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Generar reporte deportivo",
    description=(
        "Genera un reporte con datos de atletas, asistencia, evaluaciones y resultados "
        "de pruebas. Soporta filtros por club, atleta y rango de fechas. "
        "Permite exportar en formatos PDF, CSV o XLSX."
    ),
)
def generate_report(
    filters: ReportFilter,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Account, Depends(get_current_account)],
):
    """
    Genera un reporte deportivo con los filtros especificados.

    - **club_id**: Opcional. Filtra por club/escuela
    - **athlete_id**: Opcional. Filtra por deportista específico
    - **start_date**: Opcional. Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Opcional. Fecha de fin (YYYY-MM-DD)
    - **include_attendance**: Incluir datos de asistencia (default: true)
    - **include_evaluations**: Incluir datos de evaluaciones (default: true)
    - **include_tests**: Incluir resultados de pruebas (default: true)
    - **format**: Formato del archivo: pdf, csv, xlsx (default: xlsx)
    """
    try:
        # Validación de permisos (admin o coach)
        if current_user.user.role not in ["admin", "coach"]:
            raise ValidationException("No tiene permisos para generar reportes")

        # Si es coach, solo puede ver su club
        if current_user.user.role == "coach" and filters.club_id:
            if current_user.user.club_id != filters.club_id:
                raise ValidationException("No tiene permiso para acceder a este club")
        elif current_user.user.role == "coach":
            filters.club_id = current_user.user.club_id

        # Generar reporte
        report_info = report_controller.generate_report(
            db=db,
            filters=filters,
            user_dni=current_user.user.dni,
        )

        return ResponseSchema(
            status="success",
            data=report_info.model_dump(),
            message="Reporte generado exitosamente",
        )

    except ValidationException as e:
        return ResponseSchema(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return ResponseSchema(
            status="error",
            message=f"Error al generar reporte: {str(e)}",
        )


@router.get(
    "/preview",
    status_code=status.HTTP_200_OK,
    summary="Vista previa de reporte",
    description="Obtiene una vista previa en formato CSV de los datos que tendrá el reporte",
)
def preview_report(
    club_id: Annotated[int, Query(None)] = None,
    athlete_id: Annotated[int, Query(None)] = None,
    start_date: Annotated[date, Query(None)] = None,
    end_date: Annotated[date, Query(None)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[Account, Depends(get_current_account)] = None,
):
    """
    Obtiene una vista previa de los datos que contendrá el reporte.

    Parámetros:
    - **club_id**: Opcional. Filtra por club/escuela
    - **athlete_id**: Opcional. Filtra por deportista específico
    - **start_date**: Opcional. Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Opcional. Fecha de fin (YYYY-MM-DD)
    """
    try:
        # Validación de permisos
        if current_user.user.role not in ["admin", "coach"]:
            raise ValidationException("No tiene permisos para ver reportes")

        # Si es coach, solo puede ver su club
        if current_user.user.role == "coach":
            if club_id and current_user.user.club_id != club_id:
                raise ValidationException("No tiene permiso para acceder a este club")
            club_id = current_user.user.club_id

        # Crear filtros para preview
        filters = ReportFilter(
            club_id=club_id,
            athlete_id=athlete_id,
            start_date=start_date,
            end_date=end_date,
            format="csv",
            include_attendance=True,
            include_evaluations=True,
            include_tests=True,
        )

        # Recolectar datos
        report_data = report_controller.collect_report_data(db=db, filters=filters)

        # Generar CSV para preview
        csv_content = report_controller.generate_csv_report(report_data, filters)

        return StreamingResponse(
            iter([csv_content.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=reporte_preview.csv"
            },
        )

    except ValidationException as e:
        return ResponseSchema(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return ResponseSchema(
            status="error",
            message=f"Error al generar vista previa: {str(e)}",
        )


@router.get(
    "/stats",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Estadísticas de reportes",
    description="Obtiene estadísticas de datos disponibles para reportes",
)
def get_report_stats(
    club_id: Annotated[int, Query(None)] = None,
    athlete_id: Annotated[int, Query(None)] = None,
    start_date: Annotated[date, Query(None)] = None,
    end_date: Annotated[date, Query(None)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[Account, Depends(get_current_account)] = None,
):
    """
    Obtiene estadísticas sobre los datos disponibles para generar reportes.

    Retorna:
    - Total de atletas
    - Total de registros de asistencia
    - Total de evaluaciones
    - Total de resultados de pruebas
    """
    try:
        # Validación de permisos
        if current_user.user.role not in ["admin", "coach"]:
            raise ValidationException("No tiene permisos para ver estadísticas")

        # Si es coach, solo puede ver su club
        if current_user.user.role == "coach":
            if club_id and current_user.user.club_id != club_id:
                raise ValidationException("No tiene permiso para acceder a este club")
            club_id = current_user.user.club_id

        # Crear filtros
        filters = ReportFilter(
            club_id=club_id,
            athlete_id=athlete_id,
            start_date=start_date,
            end_date=end_date,
            format="csv",
        )

        # Obtener datos
        report_data = report_controller.collect_report_data(db=db, filters=filters)

        stats = {
            "total_athletes": len(report_data.get("athletes", [])),
            "total_attendance_records": len(report_data.get("attendance", [])),
            "total_evaluations": len(report_data.get("evaluations", [])),
            "total_sprint_tests": len(report_data["tests"].get("sprint", [])),
            "total_endurance_tests": len(report_data["tests"].get("endurance", [])),
            "total_yoyo_tests": len(report_data["tests"].get("yoyo", [])),
            "total_technical_assessments": len(
                report_data["tests"].get("technical", [])
            ),
            "total_tests": (
                len(report_data["tests"].get("sprint", []))
                + len(report_data["tests"].get("endurance", []))
                + len(report_data["tests"].get("yoyo", []))
                + len(report_data["tests"].get("technical", []))
            ),
        }

        return ResponseSchema(
            status="success",
            data=stats,
            message="Estadísticas obtenidas exitosamente",
        )

    except ValidationException as e:
        return ResponseSchema(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return ResponseSchema(
            status="error",
            message=f"Error al obtener estadísticas: {str(e)}",
        )
