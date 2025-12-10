from sqlalchemy import Column, String, Enum as SQLEnum
from app.models.base import BaseModel
from sqlalchemy.orm import relationship


class User(BaseModel):
    """Usuario del sistema con datos personales y relacion a cuenta."""
    
    __tablename__ = "users"
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dni = Column(String(10), unique=True, index=True, nullable=False)
    
    # Relaciones
    account = relationship(
        "Account",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    evaluations = relationship(
        "Evaluation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    @property
    def role(self):
        return self.account.role if self.account else None

    def __repr__(self):
        return f"<User(id={self.id}, dni='{self.dni}', name='{self.first_name} {self.last_name}')>"