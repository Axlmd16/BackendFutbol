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


@router.get(
    "",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Generar reporte deportivo",
    description=(
        "Genera un reporte con datos de atletas, asistencia, evaluaciones y resultados "
        "de pruebas. Soporta filtros por club, atleta y rango de fechas. "
        "Permite exportar en formatos PDF, CSV o XLSX."
    ),
)
def generate_report(
    format: Annotated[str, Query(...)] = "PDF",
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
    club_id: Annotated[int | None, Query()] = None,
    athlete_id: Annotated[int | None, Query()] = None,
    report_type: Annotated[str, Query()] = "all",
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[Account, Depends(get_current_account)] = None,
):
    """
    Genera un reporte deportivo con los filtros especificados.

    - **format**: Formato del archivo: PDF, CSV, XLSX (requerido)
    - **club_id**: Opcional. Filtra por club/escuela
    - **athlete_id**: Opcional. Filtra por deportista específico
    - **start_date**: Opcional. Fecha de inicio (YYYY-MM-DD)
    - **end_date**: Opcional. Fecha de fin (YYYY-MM-DD)
    - **report_type**: Tipo de reporte: attendance, evaluation, results, all (default: all)
    """
    try:
        # Validación de formato
        if format.upper() not in ["PDF", "CSV", "XLSX"]:
            raise ValidationException(f"Formato inválido: {format}. Use PDF, CSV o XLSX")

        # Validación de permisos
        if current_user.user.role not in ["ADMINISTRATOR", "COACH"]:
            raise ValidationException("No tiene permisos para generar reportes")

        # Crear filtros
        filters = ReportFilter(
            format=format.upper(),
            start_date=start_date,
            end_date=end_date,
            club_id=club_id,
            athlete_id=athlete_id,
            report_type=report_type,
        )

        # Si es coach, solo puede ver su club
        if current_user.user.role == "COACH":
            if club_id and current_user.club_id != club_id:
                raise ValidationException("No tiene permiso para acceder a este club")
            filters.club_id = current_user.club_id

        # Generar reporte
        file_content = report_controller.generate_report(db=db, filters=filters)

        # Determinar content type
        content_types = {
            "PDF": "application/pdf",
            "CSV": "text/csv",
            "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        content_type = content_types.get(format.upper(), "application/octet-stream")

        # Determinar extensión
        extensions = {
            "PDF": "pdf",
            "CSV": "csv",
            "XLSX": "xlsx",
        }
        ext = extensions.get(format.upper(), "file")

        return StreamingResponse(
            iter([file_content]),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=reporte.{ext}"},
        )

    except ValidationException as e:
        raise AppException(status_code=400, message=str(e))
    except Exception as e:
        raise AppException(status_code=500, message=f"Error al generar reporte: {str(e)}")



