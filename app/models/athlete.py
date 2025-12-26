from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Athlete(BaseModel):
    """Modelo de deportista."""

    __tablename__ = "athletes"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dni = Column(String(20), unique=True, index=True, nullable=False)
    type_athlete = Column(String(50), nullable=False)

    institutional_email = Column(String(100), unique=True, index=True, nullable=True)
    university_role = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    birth_date = Column(String(10), nullable=True)
    weight = Column(String(20), nullable=True)
    height = Column(String(20), nullable=True)

    tests = relationship(
        "Test", back_populates="athlete", cascade="all, delete-orphan"
    )
    attendances = relationship(
        "Attendance", back_populates="athlete", cascade="all, delete-orphan"
    )
    statistic = relationship(
        "Statistic",
        back_populates="athlete",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Athlete id={self.id} dni='{self.dni}' name="
            f"'{self.first_name} {self.last_name}' type='{self.type_athlete}'>"
        )
