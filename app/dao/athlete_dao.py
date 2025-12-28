from typing import List, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.enums.sex import Sex

from app.dao.base import BaseDAO
from app.models.athlete import Athlete


class AthleteDAO(BaseDAO[Athlete]):
    """
    DAO específico para deportistas
    """

    def __init__(self):
        super().__init__(Athlete)

    def get_all_with_filters(
        self, db: Session, filters
    ) -> Tuple[List[Athlete], int]:
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
            query = query.filter(
                self.model.type_athlete.ilike(f"%{filters.type_athlete}%")
            )

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

        # Filtro por estado activo
        if filters.is_active is not None:
            query = query.filter(self.model.is_active == filters.is_active)

        total = query.count()

        # Paginación
        items = (
            query.order_by(self.model.id.desc())
            .offset(filters.skip)
            .limit(filters.limit)
            .all()
        )

        return items, total
