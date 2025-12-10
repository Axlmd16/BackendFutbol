from sqlalchemy import Column, ForeignKey, Integer, String, Enum as SQLEnum
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

from app.models.enums.rol import Role

class Account(BaseModel):
    """Cuenta de usuario con datos de autenticacion y rol."""

    __tablename__ = "accounts"
    
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SQLEnum(Role, name="role_enum"), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Relaciones
    user = relationship(
        "User",
        back_populates="account"
    )
    
    def __repr__(self):
        return f"<Account(id={self.id}, email='{self.email}', role='{self.role.name}')>"