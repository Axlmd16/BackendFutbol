from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


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

    athlete_id = Column(
        Integer, ForeignKey("athletes.id"), nullable=False, unique=True, index=True
    )

    # Relaciones
    athlete = relationship("Athlete", back_populates="statistic")

    def __repr__(self):
        return (
            f"<Statistic id={self.id} athlete_id={self.athlete_id} "
            f"speed={self.speed} stamina={self.stamina} strength={self.strength} "
            f"agility={self.agility} matches_played={self.matches_played} "
            f"goals={self.goals} assists={self.assists} "
            f"yellow_cards={self.yellow_cards} red_cards={self.red_cards}>"
        )
