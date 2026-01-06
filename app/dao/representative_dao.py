"""DAO para representantes con métodos de filtrado y paginación."""

from typing import List, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.dao.base import BaseDAO
from app.models.representative import Representative
from app.schemas.representative_schema import RepresentativeFilter


class RepresentativeDAO(BaseDAO[Representative]):
    """DAO específico para representantes."""

    def __init__(self):
        super().__init__(Representative)

    def get_all_with_filters(
        self, db: Session, filters: RepresentativeFilter
    ) -> Tuple[List[Representative], int]:
        """
        Obtiene representantes con filtros de búsqueda y paginación.

        Returns:
            Tuple con (lista de representantes, total de registros)
        """
        query = db.query(self.model).filter(self.model.is_active.is_(True))

        # Aplicar búsqueda por nombre o DNI
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    self.model.full_name.ilike(search_term),
                    self.model.dni.ilike(search_term),
                )
            )

        # Contar total antes de paginar
        total = query.count()

        # Aplicar paginación y eager load de athletes para el conteo
        items = (
            query.options(joinedload(self.model.athletes))
            .offset(filters.skip)
            .limit(filters.limit)
            .all()
        )

        return items, total

    def get_by_dni(self, db: Session, dni: str) -> Representative | None:
        """
        Obtiene un representante por DNI.
        """
        return self.get_by_field(db, "dni", dni, only_active=True)
