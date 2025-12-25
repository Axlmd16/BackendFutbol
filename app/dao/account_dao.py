from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.account import Account


class AccountDAO(BaseDAO[Account]):
    """DAO para gestión de cuentas de usuarios."""

    def __init__(self) -> None:
        super().__init__(Account)

    
    def get_by_email(self, db: Session, email: str, only_active: bool = True):
        """Obtener una cuenta por email."""
        return self.get_by_field(db, "email", email, only_active=only_active)
