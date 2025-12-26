from typing import Optional

from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.account import Account


class AccountDAO(BaseDAO[Account]):
    """DAO para gestión de cuentas de usuarios."""

    def __init__(self) -> None:
        super().__init__(Account)

    
    def get_by_email(self, db: Session, email: str, only_active: bool = True) -> Optional[Account]:  # noqa: E501
        """Obtener una cuenta por email.

        Args:
            db: Sesión de SQLAlchemy para realizar la consulta.
            email: Correo electrónico de la cuenta a buscar.
            only_active: Si es True, limita la búsqueda a cuentas activas.

        Returns:
            Account | None: Cuenta encontrada o None si no existe/coincide el filtro.
        """
        return self.get_by_field(db, "email", email, only_active=only_active)
