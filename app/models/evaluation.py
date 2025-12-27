from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Evaluation(BaseModel):
    """Evento de evaluacion con fecha, lugar y observaciones asociadas a un evaluador"""

    __tablename__ = "evaluations"

    # Atributos de la evaluacion
    date = Column(DateTime, nullable=False, index=True)
    time = Column(String(10), nullable=False)
    location = Column(String(255), nullable=True)
    name = Column(String(100), nullable=False)
    observations = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relaciones
    user = relationship("User", back_populates="evaluations")

    tests = relationship(
        "Test", back_populates="evaluation", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Evaluation id={self.id} name={self.name} "
            f"date={self.date} time={self.time} location={self.location}>"
        )
