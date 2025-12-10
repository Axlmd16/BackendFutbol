from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, Enum as SQLEnum
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

from app.models.enums.rol import Role

class Account(BaseModel):
    """Cuenta de usuario con datos de autenticacion y rol."""

    __tablename__ = "accounts"
    
    #Atributos
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SQLEnum(Role, name="role_enum"), nullable=False)

    # Atributos para seguridad y control de acceso
    failed_attempts = Column(Integer, nullable=False, default=0)
    is_locked = Column(Boolean, nullable=False, default=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Relacioneses
    user = relationship(
        "User",
        back_populates="account"
    )
    
    def __repr__(self):
        return f"<Account(id={self.id}, email='{self.email}', role='{self.role.name}')>"