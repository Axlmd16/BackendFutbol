from typing import Optional

from sqlalchemy.orm import Session

from app.dao.account_dao import AccountDAO
from app.models.account import Account
from app.schemas.account_schema import AccountCreate, AccountUpdate


class AccountController:
    """Controlador de cuentas de usuario."""

    def __init__(self) -> None:
        self.account_dao = AccountDAO()

    #Permite listar todas las cuentas de usuario
    def list_accounts(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True,
    ) -> list[Account]:
        return self.account_dao.get_all(db, skip=skip, limit=limit, only_active=only_active)

    #Permite obtener una cuenta por su ID
    def get_account(
        self,
        db: Session,
        account_id: int,
        *,
        only_active: bool = True,
    ) -> Optional[Account]:
        return self.account_dao.get_by_id(db, account_id, only_active)

    #Permite crear una nueva cuenta de usuario
    def create_account(self, db: Session, payload: AccountCreate) -> Account:
        return self.account_dao.create(db, payload.model_dump())



    #Permite actualizar una cuenta existente 
    def update_account(
        self,
        db: Session,
        account_id: int,
        payload: AccountUpdate,
    ) -> Optional[Account]:
        data = payload.model_dump(exclude_unset=True, exclude_none=True)
        return self.account_dao.update(db, account_id, data)

    #Permite eliminar una cuenta de usuario
    def delete_account(
        self,
        db: Session,
        account_id: int,
        *,
        soft_delete: bool = True,
    ) -> bool:
        return self.account_dao.delete(db, account_id, soft_delete)
