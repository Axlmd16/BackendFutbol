from sqlalchemy import Column, ForeignKey, Integer, DateTime, String, Text
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

class Test(BaseModel):
    """Prueba base polimorfica asociada a una evaluacion y un atleta."""

    __tablename__ = "tests"
    
    type = Column(String(50))
    
    date = Column(DateTime, nullable=False, index=True)
    observations = Column(Text)
    
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False, index=True)
    
    # Relaciones
    evaluation = relationship(
        "Evaluation", 
        back_populates="tests"
    )
    
    athlete = relationship(
        "Athlete", 
        back_populates="tests"
    )
    
    # Polimorfismo
    __mapper_args__ = {
        'polymorphic_identity': 'test',
        'polymorphic_on': type
    }
    
    def __repr__(self):
        return f"<Test(id={self.id}, type='{self.type}', athlete_id={self.athlete_id}, date={self.date})>"