"""Controlador de asistencias con lógica de negocio."""

import logging
from datetime import date, datetime
from typing import Tuple

from sqlalchemy.orm import Session

from app.dao.attendance_dao import AttendanceDAO
from app.schemas.attendance_schema import AttendanceBulkCreate, AttendanceFilter
from app.utils.exceptions import AppException, ValidationException

logger = logging.getLogger(__name__)


class AttendanceController:
    """Controlador de asistencias."""

    def __init__(self):
        self.attendance_dao = AttendanceDAO()

    def create_bulk_attendance(
        self,
        db: Session,
        data: AttendanceBulkCreate,
        user_dni: str,
    ) -> Tuple[int, int]:
        """
        Crear múltiples registros de asistencia.

        Args:
            db: Sesión de base de datos
            data: Datos de las asistencias (fecha, hora, registros)
            user_dni: DNI del usuario que registra

        Returns:
            Tupla (creados, actualizados)

        Raises:
            ValidationException: Si los datos son inválidos
        """
        try:
            # Si no se proporciona hora, usar la hora actual
            if data.time:
                time_str = data.time
            else:
                time_str = datetime.now().strftime("%H:%M")

            # Validar que hay registros
            if not data.records:
                raise ValidationException("Debe proporcionar al menos un registro")

            # Convertir records a lista de diccionarios
            records_data = [
                {
                    "athlete_id": record.athlete_id,
                    "is_present": record.is_present,
                    "justification": record.justification,
                }
                for record in data.records
            ]

            # Crear o actualizar registros
            created, updated = self.attendance_dao.create_or_update_bulk(
                db=db,
                target_date=data.attendance_date,
                time_str=time_str,
                user_dni=user_dni,
                records=records_data,
            )

            logger.info(
                f"Attendance bulk created/updated: {created} created, {updated} updated"
            )
            return created, updated

        except ValidationException:
            raise
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating bulk attendance: {str(e)}")
            raise AppException(f"Error al crear asistencias: {str(e)}") from e

    def get_attendances_by_date(
        self,
        db: Session,
        filters: AttendanceFilter,
    ) -> Tuple[list, int]:
        """
        Obtener asistencias por fecha con filtros.

        Args:
            db: Sesión de base de datos
            filters: Filtros de búsqueda

        Returns:
            Tupla con lista de asistencias formateadas y total
        """
        try:
            attendances, total = self.attendance_dao.get_by_date(
                db=db,
                target_date=filters.attendance_date,
                type_athlete=filters.type_athlete,
                search=filters.search,
                skip=filters.skip,
                limit=filters.limit,
            )

            # Formatear respuesta
            formatted = []
            for att in attendances:
                formatted.append(
                    {
                        "id": att.id,
                        "date": att.date.isoformat() if att.date else None,
                        "time": att.time,
                        "is_present": att.is_present,
                        "justification": att.justification,
                        "athlete_id": att.athlete_id,
                        "athlete_name": att.athlete.full_name if att.athlete else None,
                        "athlete_dni": att.athlete.dni if att.athlete else None,
                        "athlete_type": att.athlete.type_athlete if att.athlete else None,
                        "user_dni": att.user_dni,
                        "created_at": (
                            att.created_at.isoformat() if att.created_at else None
                        ),
                        "is_active": att.is_active,
                    }
                )

            return formatted, total

        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error getting attendances by date: {str(e)}")
            raise AppException(f"Error al obtener asistencias: {str(e)}") from e

    def get_attendance_summary(self, db: Session, target_date: date) -> dict:
        """
        Obtener resumen de asistencia por fecha.

        Args:
            db: Sesión de base de datos
            target_date: Fecha a consultar

        Returns:
            Dict con estadísticas de asistencia
        """
        return self.attendance_dao.get_attendance_summary_by_date(db, target_date)
