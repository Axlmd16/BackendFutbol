"""DAO específico para asistencias con métodos de consulta por fecha y atleta."""

import logging
from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app.dao.base import BaseDAO
from app.models.athlete import Athlete
from app.models.attendance import Attendance
from app.utils.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class AttendanceDAO(BaseDAO[Attendance]):
    """DAO específico para asistencias."""

    def __init__(self):
        super().__init__(Attendance)

    def get_by_date(
        self,
        db: Session,
        target_date: date,
        type_athlete: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Attendance], int]:
        """
        Obtener asistencias por fecha con filtros opcionales.

        Args:
            db: Sesión de base de datos
            target_date: Fecha para filtrar
            type_athlete: Tipo de atleta (opcional)
            search: Búsqueda por nombre o DNI (opcional)
            skip: Offset para paginación
            limit: Límite de resultados

        Returns:
            Tupla con lista de asistencias y total
        """
        try:
            # Convertir date a datetime para comparar (inicio y fin del día)
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            query = (
                db.query(Attendance)
                .join(Athlete, Attendance.athlete_id == Athlete.id)
                .options(joinedload(Attendance.athlete))
                .filter(
                    and_(
                        Attendance.date >= start_of_day,
                        Attendance.date <= end_of_day,
                        Attendance.is_active,
                    )
                )
            )

            # Filtrar por tipo de atleta
            if type_athlete:
                query = query.filter(Athlete.type_athlete == type_athlete)

            # Búsqueda por nombre o DNI
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (Athlete.full_name.ilike(search_term))
                    | (Athlete.dni.ilike(search_term))
                )

            # Contar total antes de paginar
            total = query.count()

            # Aplicar paginación y ordenar
            items = (
                query.order_by(Athlete.full_name.asc()).offset(skip).limit(limit).all()
            )

            return items, total

        except Exception as e:
            logger.error(f"Error getting attendances by date: {str(e)}")
            raise DatabaseException("Error al obtener asistencias por fecha") from e

    def get_by_athlete_and_date(
        self, db: Session, athlete_id: int, target_date: date
    ) -> Optional[Attendance]:
        """
        Verificar si ya existe un registro de asistencia para un atleta en una fecha.

        Args:
            db: Sesión de base de datos
            athlete_id: ID del atleta
            target_date: Fecha a verificar

        Returns:
            Registro de asistencia si existe, None si no
        """
        try:
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            return (
                db.query(Attendance)
                .filter(
                    and_(
                        Attendance.athlete_id == athlete_id,
                        Attendance.date >= start_of_day,
                        Attendance.date <= end_of_day,
                        Attendance.is_active,
                    )
                )
                .first()
            )

        except Exception as e:
            logger.error(
                f"Error checking attendance for athlete {athlete_id}: {str(e)}"
            )
            raise DatabaseException("Error al verificar asistencia") from e

    def create_or_update_bulk(
        self,
        db: Session,
        target_date: date,
        time_str: str,
        user_dni: str,
        records: List[dict],
    ) -> Tuple[int, int]:
        """
        Crear o actualizar asistencias en lote.

        Args:
            db: Sesión de base de datos
            target_date: Fecha de la asistencia
            time_str: Hora de la asistencia (HH:MM)
            user_dni: DNI del usuario que registra
            records: Lista de registros [{athlete_id, is_present, justification}]

        Returns:
            Tupla (creados, actualizados)
        """
        try:
            created = 0
            updated = 0
            attendance_datetime = datetime.combine(target_date, datetime.min.time())

            # Identificar IDs que vienen en el payload
            payload_athlete_ids = [r["athlete_id"] for r in records]

            # 1. ELIMINAR registros que NO están en el payload para esta fecha
            # (Si no está en el payload, es porque no está presente)
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            db.query(Attendance).filter(
                and_(
                    Attendance.date >= start_of_day,
                    Attendance.date <= end_of_day,
                    Attendance.is_active.is_(True),
                    Attendance.athlete_id.notin_(payload_athlete_ids),
                )
            ).delete(synchronize_session=False)

            # 2. UPSERT de los registros que SI vienen
            for record in records:
                athlete_id = record["athlete_id"]
                is_present = record.get("is_present", True)
                justification = record.get("justification")

                # Si está presente, limpiar justificación
                if is_present:
                    justification = None

                # Verificar si ya existe
                existing = self.get_by_athlete_and_date(db, athlete_id, target_date)

                if existing:
                    # Actualizar existente
                    existing.time = time_str
                    existing.is_present = is_present
                    existing.justification = justification
                    existing.user_dni = user_dni
                    updated += 1
                else:
                    # Crear nuevo
                    new_attendance = Attendance(
                        date=attendance_datetime,
                        time=time_str,
                        is_present=is_present,
                        justification=justification,
                        user_dni=user_dni,
                        athlete_id=athlete_id,
                    )
                    db.add(new_attendance)
                    created += 1

            db.commit()
            return created, updated

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating/updating bulk attendances: {str(e)}")
            raise DatabaseException("Error al crear asistencias en lote") from e

    def get_attendance_summary_by_date(self, db: Session, target_date: date) -> dict:
        """
        Obtener resumen de asistencia por fecha.

        Returns:
            Dict con total, presentes y ausentes
        """
        try:
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            total = (
                db.query(func.count(Attendance.id))
                .filter(
                    and_(
                        Attendance.date >= start_of_day,
                        Attendance.date <= end_of_day,
                        Attendance.is_active,
                    )
                )
                .scalar()
            )

            present = (
                db.query(func.count(Attendance.id))
                .filter(
                    and_(
                        Attendance.date >= start_of_day,
                        Attendance.date <= end_of_day,
                        Attendance.is_present,
                        Attendance.is_active,
                    )
                )
                .scalar()
            )

            return {
                "total": total or 0,
                "present": present or 0,
                "absent": (total or 0) - (present or 0),
            }

        except Exception as e:
            logger.error(f"Error getting attendance summary: {str(e)}")
            return {"total": 0, "present": 0, "absent": 0}

    def get_existing_dates(self, db: Session) -> List[date]:
        """
        Obtener lista de fechas que tienen registros de asistencia.

        Returns:
            Lista de fechas ordenadas descendente
        """
        try:
            dates = (
                db.query(Attendance.date)
                .filter(Attendance.is_active.is_(True))
                .distinct()
                .order_by(Attendance.date.desc())
                .all()
            )
            return [d[0].date() for d in dates]
        except Exception as e:
            logger.error(f"Error getting existing dates: {str(e)}")
            raise DatabaseException("Error al obtener fechas de asistencia") from e
