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
    
    # Campos para inscripción UNL
    # Email institucional único de la comunidad universitaria
    institutional_email = Column(String(100), unique=True, index=True, nullable=True)
    # Rol en la institución: STUDENT, TEACHER, ADMIN, WORKER
    university_role = Column(String(50), nullable=True)
    # Datos físicos del deportista
    phone = Column(String(20), nullable=True)
    birth_date = Column(String(10), nullable=True)  # Formato: YYYY-MM-DD
    weight = Column(String(20), nullable=True)  # En kg
    height = Column(String(20), nullable=True)  # En cm
    
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