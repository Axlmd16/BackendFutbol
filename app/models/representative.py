from sqlalchemy import Column, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums.relationship import Relationship


class Representative(BaseModel):
    """Representante legal de atletas menores de edad."""

    __tablename__ = "representatives"

    external_person_id = Column(String(36), unique=True, index=True, nullable=False)

    full_name = Column(String(200), nullable=False)
    # 20 caracteres para soportar: Cédula (10), RUC (13), Pasaporte (hasta 15)
    dni = Column(String(20), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    relationship_type = Column(
        SQLEnum(Relationship, name="relationship_enum"), nullable=False
    )

    # Relaciones
    athletes = relationship("Athlete", back_populates="representative")

    def __repr__(self):
        return f"<Representative {self.full_name} - DNI: {self.dni}>"
