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
from datetime import date, datetime

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
    format: Annotated[str | None, Query()] = "PDF",
    start_date: Annotated[str | None, Query()] = None,
    end_date: Annotated[str | None, Query()] = None,
    club_id: Annotated[int | None, Query()] = None,
    athlete_id: Annotated[int | None, Query()] = None,
    report_type: Annotated[str | None, Query()] = "all",
    include_attendance: Annotated[str | bool | None, Query()] = True,
    include_evaluations: Annotated[str | bool | None, Query()] = True,
    include_tests: Annotated[str | bool | None, Query()] = True,
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
        fmt = (format or "PDF").upper()
        if fmt not in ["PDF", "CSV", "XLSX"]:
            raise ValidationException(f"Formato inválido: {format}. Use PDF, CSV o XLSX")

        # Validación de permisos
        if current_user.user.role not in ["ADMINISTRATOR", "COACH"]:
            raise ValidationException("No tiene permisos para generar reportes")

        # Normalizar fechas: strings vacíos -> None
        parsed_start = None
        parsed_end = None
        try:
            if start_date:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationException("Fechas inválidas. Usa formato YYYY-MM-DD")

        # Normalizar booleans (acepta "true"/"false"/1/0)
        def to_bool(val: str | bool | None, default: bool) -> bool:
            if val is None or val == "":
                return default
            if isinstance(val, bool):
                return val
            v = str(val).strip().lower()
            if v in ["true", "1", "yes", "on"]:
                return True
            if v in ["false", "0", "no", "off"]:
                return False
            return default

        inc_att = to_bool(include_attendance, True)
        inc_eval = to_bool(include_evaluations, True)
        inc_tests = to_bool(include_tests, True)

        # Report type por defecto
        rpt_type = (report_type or "all").strip() or "all"

        # Crear filtros
        filters = ReportFilter(
            format=fmt.lower(),
            start_date=parsed_start,
            end_date=parsed_end,
            club_id=club_id,
            athlete_id=athlete_id,
            report_type=rpt_type,
            include_attendance=inc_att,
            include_evaluations=inc_eval,
            include_tests=inc_tests,
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
        content_type = content_types.get(fmt, "application/octet-stream")

        # Determinar extensión
        extensions = {
            "PDF": "pdf",
            "CSV": "csv",
            "XLSX": "xlsx",
        }
        ext = extensions.get(fmt, "file")

        # Usamos el buffer directamente para no duplicar memoria
        file_content.seek(0)
        return StreamingResponse(
            file_content,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=reporte.{ext}"},
        )

    except ValidationException as e:
        raise AppException(status_code=400, message=str(e))
    except Exception as e:
        raise AppException(status_code=500, message=f"Error al generar reporte: {str(e)}")



