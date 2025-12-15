import datetime
from sqlalchemy import Column, Float, String, Integer, ForeignKey, Enum as SQLEnum, Date

from app.models.base import BaseModel
from sqlalchemy.orm import relationship

from app.models.enums.sex import Sex

class Athlete(BaseModel):
    """Deportista asociado a una persona del MS de usuarios."""
    
    __tablename__ = "athletes"
    
    external_person_id = Column(String(36), unique=True, index=True, nullable=False)
    
    full_name = Column(String(200), nullable=False)
    dni = Column(String(10), unique=True, index=True, nullable=False)
    
    # Datos específicos del atleta
    type_athlete = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    sex = Column(SQLEnum(Sex, name="sex_enum"), nullable=False)
    
    representative_id = Column(
        Integer,
        ForeignKey("representatives.id"),
        nullable=True,
        index=True
    )
    
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
    
    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def is_adult(self):
        return self.age >= 18 if self.age is not None else None
    
    @property
    def representative_name(self):
        return self.representative.full_name if self.representative else None
    
    @property
    def representative_dni(self):
        return self.representative.dni if self.representative else None
    
    def __repr__(self):
        return f"<Athlete {self.full_name} - DNI: {self.dni}>"
