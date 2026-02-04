from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.dao.base import BaseDAO
from app.models.account import Account


class AccountDAO(BaseDAO[Account]):
    """DAO para gestión de cuentas de usuarios."""

    def __init__(self) -> None:
        super().__init__(Account)

    def get_by_email(
        self, db: Session, email: str, only_active: bool = True
    ) -> Optional[Account]:  # noqa: E501
        """Obtener una cuenta por email con usuario precargado.

        Args:
            db: Sesión de SQLAlchemy para realizar la consulta.
            email: Correo electrónico de la cuenta a buscar.
            only_active: Si es True, limita la búsqueda a cuentas activas.

        Returns:
            Account | None: Cuenta encontrada o None si no existe/coincide el filtro.
        """
        query = (
            db.query(Account)
            .options(joinedload(Account.user))
            .filter(Account.email == email)
        )
        if only_active:
            query = query.filter(Account.is_active == True)  # noqa: E712
        return query.first()
