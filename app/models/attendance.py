from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Text, Integer
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

class Attendance(BaseModel):
    """Registro de asistencia por atleta con hora, presencia y justificacion."""

    __tablename__ = "attendances"
    
    date = Column(DateTime, nullable=False, index=True)
    time = Column(String(10), nullable=False)
    is_present = Column(Boolean, nullable=False, default=False)
    justification = Column(Text, nullable=True)
    evaluator_dni = Column(String(20), nullable=False, index=True)  # Clave externa a Evaluator.dni
    
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False, index=True)
    
    # Relaciones
    athlete = relationship(
        "Athlete", 
        back_populates="attendances"
    )
    
    def __repr__(self):
        return f"<Attendance(id={self.id}, athlete_id={self.athlete_id}, date={self.date}, present={self.is_present})>"