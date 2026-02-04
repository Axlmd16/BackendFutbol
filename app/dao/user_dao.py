from typing import List, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.account import Account
from app.models.enums.rol import Role
from app.models.user import User
from app.schemas.user_schema import UserFilter

# Mapeo de aliases del frontend a valores del enum
ROLE_ALIASES = {
    "admin": Role.ADMINISTRATOR,
    "administrator": Role.ADMINISTRATOR,
    "entrenador": Role.COACH,
    "coach": Role.COACH,
    "pasante": Role.INTERN,
    "intern": Role.INTERN,
}


class UserDAO(BaseDAO[User]):
    """DAO para gestión de usuarios del sistema."""

    def __init__(self) -> None:
        super().__init__(User)

    def _resolve_role(self, role_str: str) -> Role | None:
        """Convierte un string de rol a su enum correspondiente."""
        if not role_str:
            return None

        role_lower = role_str.lower().strip()

        # Buscar en aliases
        if role_lower in ROLE_ALIASES:
            return ROLE_ALIASES[role_lower]

        # Intentar valor directo del enum
        try:
            return Role(role_str)
        except ValueError:
            pass

        # Intentar por nombre del enum
        return getattr(Role, role_str.upper(), None)

    def _apply_search_filter(self, query, search: str):
        """Aplica filtro de búsqueda por nombre, DNI o email."""
        if search:
            search_norm = search.strip()
            query = query.filter(
                or_(
                    self.model.full_name.ilike(f"%{search_norm}%"),
                    self.model.dni.ilike(f"%{search_norm}%"),
                    self.model.account.has(Account.email.ilike(f"%{search_norm}%")),
                )
            )
        return query

    def _paginate_query(self, query, filters) -> Tuple[List[User], int]:
        """Aplica paginación y retorna items con total."""
        total = query.count()
        items = (
            query.order_by(self.model.id.desc())
            .offset(filters.skip)
            .limit(filters.limit)
            .all()
        )
        return items, total

    def get_all_with_filters(
        self, db: Session, filters: UserFilter
    ) -> Tuple[List[User], int]:
        query = db.query(self.model)

        # Filtrar por estado activo/inactivo (None = todos)
        if filters.is_active is not None:
            query = query.filter(self.model.is_active.is_(filters.is_active))

        if filters.role:
            role_enum = self._resolve_role(filters.role)
            if role_enum:
                query = query.filter(self.model.account.has(role=role_enum))

        query = self._apply_search_filter(query, filters.search)

        return self._paginate_query(query, filters)

    def get_interns_with_filters(self, db: Session, filters) -> Tuple[List[User], int]:
        """
        Obtiene usuarios con rol INTERN con paginación y búsqueda.
        """
        query = db.query(self.model).filter(self.model.account.has(role=Role.INTERN))

        query = self._apply_search_filter(query, filters.search)

        return self._paginate_query(query, filters)
