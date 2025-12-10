from datetime import datetime
from typing import Optional
from typing import Optional

from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.account import Account


class AccountDAO(BaseDAO[Account]):
    """DAO para gestión de cuentas de usuarios."""

    def __init__(self) -> None:
        super().__init__(Account)


    #Permite obtener una cuenta por su email
    def get_by_email(
        self,
        db: Session,
        email: str,
        *,
        only_active: bool = True,
    ) -> Optional[Account]:
        return self.get_by_field(db, "email", email, only_active)
   

    #Permite actualizar la contraseña de una cuenta
    def update_password(
        self,
        db: Session,
        account_id: int,
        new_password_hash: str,
    ) -> Optional[Account]:
        account = self.get_by_id(db, account_id, only_active=False)
        if not account:
            return None

        account.password = new_password_hash
        db.commit()
        db.refresh(account)
        return account
