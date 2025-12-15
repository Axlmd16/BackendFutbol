from sqlalchemy import Column, String
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

class Representative(BaseModel):
    """Representante legal de atletas menores de edad."""
    
    __tablename__ = "representatives"
    
    external_person_id = Column(String(36), unique=True, index=True, nullable=False)
    
    full_name = Column(String(200), nullable=False)
    dni = Column(String(10), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    
    relationship_type = Column(String(50), nullable=False)
    
    # Relaciones
    athletes = relationship(
        "Athlete",
        back_populates="representative"
    )
    
    def __repr__(self):
        return f"<Representative {self.full_name} - DNI: {self.dni}>"
