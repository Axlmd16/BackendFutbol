from sqlalchemy import Column, String, Date, Integer, ForeignKey
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

class Athlete(BaseModel):
    """Deportista con datos de identificacion y relaciones a pruebas y estadisticas."""

    __tablename__ = "athletes"
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dni = Column(String(20), unique=True, index=True, nullable=False)
    birth_date = Column(Date, nullable=True, comment="Fecha de nacimiento del deportista")
    sex = Column(String(10), nullable=True, comment="Sexo del deportista (M/F)")
    type_athlete = Column(String(50), nullable=False)
    
    # Relación con representante (solo para menores de edad)
    representative_id = Column(Integer, ForeignKey("representatives.id"), nullable=True, comment="ID del representante legal si es menor de edad")
    parental_authorization = Column(String(10), nullable=True, comment="Autorización parental (SI/NO)")
    
    # Relaciones
    representative = relationship(
        "Representative",
        back_populates="athletes"
    )
    
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