from sqlalchemy import Column, ForeignKey, Integer, Float
from app.models.test import Test

class EnduranceTest(Test):
    __tablename__ = "endurance_tests"
    
    id = Column(Integer, ForeignKey("tests.id"), primary_key=True)
    
    min_duration = Column(Integer, nullable=False)
    total_distance_m = Column(Float, nullable=False)
    
    # Polimorfismo
    __mapper_args__ = {
        'polymorphic_identity': 'endurance_test',
    }
    
    # Propiedades calculadas
    @property
    def pace_min_per_km(self) -> float:
        """Ritmo en minutos por kilómetro (calculado)"""
        if self.total_distance_m and self.total_distance_m > 0:
            distance_km = self.total_distance_m / 1000
            return self.min_duration / distance_km
        return None
    
    @property
    def estimated_vo2max(self) -> float:
        """VO2 máximo estimado en ml/kg/min (calculado)
        Fórmula simplificada: VO2max = (distancia_metros - 504.9) / 44.73
        """
        if self.total_distance_m:
            return (self.total_distance_m - 504.9) / 44.73
        return None
    
    def __repr__(self):
        return f"<EnduranceTest(id={self.id}, athlete_id={self.athlete_id}, duration={self.min_duration}min, distance={self.total_distance_m}m)>"