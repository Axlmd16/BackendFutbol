from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

class Evaluation(BaseModel):
    __tablename__ = "evaluations"
    
    # Atributos de la evaluacion
    date = Column(DateTime, nullable=False, index=True)
    time = Column(String(10), nullable=False)
    location = Column(String(255), nullable=True)
    name = Column(String(100), nullable=False)
    observations = Column(Text, nullable=True)
    
    evaluator_id = Column(Integer, ForeignKey("evaluators.id"), nullable=False, index=True)
    
    # Relaciones
    evaluator = relationship(
        "Evaluator", 
        back_populates="evaluations"
    )
    
    tests = relationship(
        "Test",
        back_populates="evaluation",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Evaluation(id={self.id}, name='{self.name}', date={self.date}, evaluator_id={self.evaluator_id})>"