from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """Usuario del sistema asociado a una persona del MS de usuarios."""

    __tablename__ = "users"

    external_person_id = Column(String(36), nullable=True, index=True)

    full_name = Column(String(200), nullable=False)
    dni = Column(String(10), unique=True, index=True, nullable=False)

    # Relaciones
    account = relationship(
        "Account",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    evaluations = relationship(
        "Evaluation",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def role(self):
        return self.account.role if self.account else None

    def __repr__(self):
        return f"<User id={self.id} dni={self.dni} full_name={self.full_name}>"
