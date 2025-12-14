from sqlalchemy import Column, ForeignKey, Integer, String, Enum as SQLEnum

from app.models.base import BaseModel
from sqlalchemy.orm import relationship
from app.models.enums.rol import Role


class Account(BaseModel):
    """Cuenta de usuario en el club, enlazada a la cuenta del MS de usuarios."""

    __tablename__ = "accounts"

    external_account_id = Column(String(36), unique=True, index=True, nullable=False)
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
        return f"<Account id={self.id} external_account_id={self.external_account_id} role={self.role}>"
