from sqlalchemy import Column, String
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

class Athlete(BaseModel):
    """Deportista con datos de identificacion y relaciones a pruebas y estadisticas."""

    __tablename__ = "athletes"
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dni = Column(String(20), unique=True, index=True, nullable=False)
    type_athlete = Column(String(50), nullable=False)
    
    # Relaciones
    tests = relationship(
        "Test",
        back_populates="athlete",
        cascade="all, delete-orphan"
    )
    
    attendances = relationship(
        "Attendance",
        back_populates="athlete",
        cascade="all, delete-orphan"
    )
    
    statistic = relationship(
        "Statistic",
        back_populates="athlete",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Athlete(id={self.id}, dni='{self.dni}', name='{self.first_name} {self.last_name}', type='{self.type_athlete}')>"