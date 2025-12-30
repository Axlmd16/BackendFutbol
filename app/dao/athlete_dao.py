from typing import List, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.athlete import Athlete
from app.models.enums.sex import Sex


class AthleteDAO(BaseDAO[Athlete]):
    """
    DAO específico para deportistas
    """

    def __init__(self):
        super().__init__(Athlete)

    def get_all_with_filters(self, db: Session, filters) -> Tuple[List[Athlete], int]:
        """
        Obtiene atletas con filtros y paginación.
        """
        query = db.query(self.model)

        # Filtro por búsqueda (nombre o DNI)
        if filters.search:
            search_norm = filters.search.strip()
            query = query.filter(
                or_(
                    self.model.full_name.ilike(f"%{search_norm}%"),
                    self.model.dni.ilike(f"%{search_norm}%"),
                )
            )

        # Filtro por tipo de atleta
        if filters.type_athlete:
            # Extraer valor del enum si es necesario
            type_value = getattr(filters.type_athlete, "value", filters.type_athlete)
            query = query.filter(self.model.type_athlete.ilike(f"%{type_value}%"))

        # Filtro por sexo (acepta enum, string o alias)
        if getattr(filters, "sex", None):
            sex_value = filters.sex
            sex_enum: Sex | None = None
            # Si ya es enum Sex
            if isinstance(sex_value, Sex):
                sex_enum = sex_value
            else:
                # Normalizar strings como 'MALE', 'FEMALE', 'OTHER'
                try:
                    sex_enum = Sex(str(sex_value).upper())
                except Exception:
                    sex_enum = None
            if sex_enum:
                query = query.filter(self.model.sex == sex_enum)

        # Filtro por estado activo (tolerante si atributo no existe)
        is_active = getattr(filters, "is_active", None)
        if is_active is not None:
            query = query.filter(self.model.is_active == is_active)

        total = query.count()

        # Paginación
        # Paginación con tolerancia si no existen propiedades
        skip = getattr(filters, "skip", 0)
        limit = getattr(filters, "limit", 10)
        items = query.order_by(self.model.id.desc()).offset(skip).limit(limit).all()

        return items, total
