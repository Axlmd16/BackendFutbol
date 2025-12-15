from typing import Optional

from sqlalchemy.orm import Session

from app.dao.account_dao import AccountDAO
from app.models.account import Account


class AccountController:
    """Controlador de cuentas de usuario."""

    def __init__(self) -> None:
        self.account_dao = AccountDAO()


    def list_accounts(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True,
    ) -> list[Account]:
        """Listar todas las cuentas de usuario."""
        return self.account_dao.get_all(db, skip=skip, limit=limit, only_active=only_active)


    def get_account(
        self,
        db: Session,
        account_id: int,
        *,
        only_active: bool = True,
    ) -> Optional[Account]:
        """Obtiene una cuenta por su ID."""
        return self.account_dao.get_by_id(db, account_id, only_active)

    def get_by_external(
        self,
        db: Session,
        external_account_id: str,
        *,
        only_active: bool = True,
    ) -> Optional[Account]:
        """Obtiene una cuenta por su external_account_id."""
        return self.account_dao.get_by_external(db, external_account_id, only_active=only_active)
