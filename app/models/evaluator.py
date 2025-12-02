from sqlalchemy import Column, String
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

class Evaluator(BaseModel):
    __tablename__ = "evaluators"
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dni = Column(String(20), unique=True, index=True, nullable=False)
    
    # Relaciones
    evaluations = relationship(
        'Evaluation',                   
        back_populates='evaluator',     
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Evaluator(id={self.id}, dni='{self.dni}', name='{self.first_name} {self.last_name}')>"