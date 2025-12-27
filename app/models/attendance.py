from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Attendance(BaseModel):
    """Registro de asistencia por atleta con hora, presencia y justificacion."""

    __tablename__ = "attendances"

    date = Column(DateTime, nullable=False, index=True)
    time = Column(String(10), nullable=False)
    is_present = Column(Boolean, nullable=False, default=False)
    justification = Column(Text, nullable=True)
    user_dni = Column(
        String(10), nullable=False, index=True
    )  # Clave externa a User.dni

    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False, index=True)

    # Relaciones
    athlete = relationship("Athlete", back_populates="attendances")

    def __repr__(self):
        return (
            f"<Attendance(id={self.id}, "
            f"athlete_id={self.athlete_id}, "
            f"date={self.date}, "
            f"present={self.is_present})>"
        )
