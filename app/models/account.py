from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums.rol import Role


class Account(BaseModel):
    """Cuenta de usuario en el club"""

    __tablename__ = "accounts"

    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(Role, name="role_enum"), nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Relaciones
    user = relationship(
        "User",
        back_populates="account",
    )

    def __repr__(self):
        return f"<Account id={self.id} email={self.email} role={self.role}>"
