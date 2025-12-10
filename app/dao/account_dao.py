from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.dao.base import BaseDAO
from app.models.account import Account


class AccountDAO(BaseDAO[Account]):
    """DAO para gestión de cuentas de usuarios."""

    def __init__(self) -> None:
        super().__init__(Account)


    #Permite obtener una cuenta por correo electrónico
    def get_by_email(
        self,
        db: Session,
        email: str,
        *,
        only_active: bool = True,
    ) -> Optional[Account]:
        return self.get_by_field(db, "email", email, only_active)



    #Permite incrementar el contador de intentos fallidos
    def increment_failed_attempts(
        self,
        db: Session,
        account_id: int,
    ) -> Optional[Account]:
        account = self.get_by_id(db, account_id, only_active=False)
        if not account:
            return None

        account.failed_attempts += 1
        db.commit()
        db.refresh(account)
        return account


    #Permite reiniciar el contador de intentos fallidos
    def reset_failed_attempts(
        self,
        db: Session,
        account_id: int,
    ) -> Optional[Account]:
        account = self.get_by_id(db, account_id, only_active=False)
        if not account:
            return None

        account.failed_attempts = 0
        db.commit()
        db.refresh(account)
        return account


   #Permite establecer el estado de bloqueo y la ventana de liberación
    def set_lock_state(
        self,
        db: Session,
        account_id: int,
        *,
        is_locked: bool,
        locked_until: Optional[datetime] = None,
    ) -> Optional[Account]:
        """Actualizar el estado de bloqueo y ventana de liberación."""
        account = self.get_by_id(db, account_id, only_active=False)
        if not account:
            return None

        account.is_locked = is_locked
        account.locked_until = locked_until
        db.commit()
        db.refresh(account)
        return account



    #Permite registrar el último inicio de sesión exitoso
    def touch_login(
        self,
        db: Session,
        account_id: int,
        *,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Account]:
        account = self.get_by_id(db, account_id, only_active=False)
        if not account:
            return None

        account.last_login = timestamp or datetime.utcnow()
        account.last_activity = account.last_login
        db.commit()
        db.refresh(account)
        return account



    #Permite actualizar la marca de tiempo de última actividad
    def touch_activity(
        self,
        db: Session,
        account_id: int,
        *,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Account]:
        account = self.get_by_id(db, account_id, only_active=False)
        if not account:
            return None

        account.last_activity = timestamp or datetime.utcnow()
        db.commit()
        db.refresh(account)
        return account

    

    #Permite actualizar la contraseña hasheada
    def update_password(
        self,
        db: Session,
        account_id: int,
        new_password_hash: str,
        *,
        reset_security_state: bool = True,
    ) -> Optional[Account]:
        account = self.get_by_id(db, account_id, only_active=False)
        if not account:
            return None

        account.password = new_password_hash
        if reset_security_state:
            account.failed_attempts = 0
            account.is_locked = False
            account.locked_until = None

        db.commit()
        db.refresh(account)
        return account
