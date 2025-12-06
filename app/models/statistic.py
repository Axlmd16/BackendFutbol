from sqlalchemy import Column, ForeignKey, Integer, Float
from app.models.base import BaseModel
from sqlalchemy.orm import relationship

class Statistic(BaseModel):
    """Perfil estadistico del atleta con metricas fisicas y de juego."""

    __tablename__ = "statistics"
    
    speed = Column(Float, nullable=True)
    stamina = Column(Float, nullable=True)
    strength = Column(Float, nullable=True)
    agility = Column(Float, nullable=True)
    
    matches_played = Column(Integer, nullable=False, default=0)
    goals = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    yellow_cards = Column(Integer, nullable=False, default=0)
    red_cards = Column(Integer, nullable=False, default=0)
    
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False, unique=True, index=True)    
    
    # Relaciones
    athlete = relationship(
        "Athlete", 
        back_populates="statistic"
    )
    
    def __repr__(self):
        return f"<Statistic(id={self.id}, athlete_id={self.athlete_id}, matches={self.matches_played}, goals={self.goals})>"