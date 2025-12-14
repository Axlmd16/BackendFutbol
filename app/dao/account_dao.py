from typing import Optional

from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.account import Account


class AccountDAO(BaseDAO[Account]):
    """DAO para gestión de cuentas de usuarios."""

    def __init__(self) -> None:
        super().__init__(Account)

    def get_by_external(
        self,
        db: Session,
        external_account_id: str,
        *,
        only_active: bool = True,
    ) -> Optional[Account]:
        """Obtiene una cuenta por su external_account_id."""
        return self.get_by_field(db, "external_account_id", external_account_id, only_active)
   
