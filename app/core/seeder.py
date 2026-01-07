"""Seeder para crear datos iniciales en la base de datos."""

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.account import Account
from app.models.enums.rol import Role
from app.models.user import User
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


def seed_default_admin(db: Session) -> None:
    """
    Crea el usuario administrador por defecto si no existe.

    Utiliza las variables de configuración:
    - DEFAULT_ADMIN_EMAIL
    - DEFAULT_ADMIN_PASSWORD
    - DEFAULT_ADMIN_DNI
    - DEFAULT_ADMIN_NAME
    """
    # Verificar si ya existe una cuenta con el email de admin
    existing_account = (
        db.query(Account).filter(Account.email == settings.DEFAULT_ADMIN_EMAIL).first()
    )

    if existing_account:
        logger.info(f"✅ Admin ya existe: {settings.DEFAULT_ADMIN_EMAIL}")
        return

    # Verificar si ya existe un usuario con el DNI de admin
    existing_user = (
        db.query(User).filter(User.dni == settings.DEFAULT_ADMIN_DNI).first()
    )

    if existing_user:
        logger.info(f"✅ Usuario admin con DNI {settings.DEFAULT_ADMIN_DNI} ya existe")
        return

    try:
        # Crear el usuario
        admin_user = User(
            external="admin-system-default",
            full_name=settings.DEFAULT_ADMIN_NAME,
            dni=settings.DEFAULT_ADMIN_DNI,
        )
        db.add(admin_user)
        db.flush()  # Para obtener el ID

        # Crear la cuenta
        admin_account = Account(
            email=settings.DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            role=Role.ADMINISTRATOR,
            user_id=admin_user.id,
        )
        db.add(admin_account)
        db.commit()

        logger.info(
            f"👤 Admin creado exitosamente:\n"
            f"   Email: {settings.DEFAULT_ADMIN_EMAIL}\n"
            f"   Password: {settings.DEFAULT_ADMIN_PASSWORD}\n"
            f"   DNI: {settings.DEFAULT_ADMIN_DNI}\n"
            f"   Nombre: {settings.DEFAULT_ADMIN_NAME}"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al crear admin por defecto: {e}")
        raise
