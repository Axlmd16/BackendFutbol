from sqlalchemy import Column, ForeignKey, Integer, String, Float
from app.models.test import Test

class YoyoTest(Test):
    __tablename__ = "yoyo_tests"
    
    id = Column(Integer, ForeignKey("tests.id"), primary_key=True)
    
    shuttle_count = Column(Integer, nullable=False)
    final_level = Column(String(10), nullable=False)  # Formato: "16.3", "18.2", etc.
    failures = Column(Integer, nullable=False)
    
    # Polimorfismo
    __mapper_args__ = {
        'polymorphic_identity': 'yoyo_test',
    }
    
    # Propiedades calculadas
    @property
    def total_distance(self) -> float:
        """Distancia total recorrida en metros (calculada)
        Cada shuttle = 20 metros (ida y vuelta)
        """
        return self.shuttle_count * 20.0
    
    @property
    def vo2_max(self) -> float:
        """VO2 máximo estimado en ml/kg/min (calculado)
        Fórmula: VO2max = distancia_total * 0.0084 + 36.4
        """
        if self.total_distance:
            return self.total_distance * 0.0084 + 36.4
        return None
    
    def __repr__(self):
        return f"<YoyoTest(id={self.id}, athlete_id={self.athlete_id}, level='{self.final_level}', shuttles={self.shuttle_count})>"