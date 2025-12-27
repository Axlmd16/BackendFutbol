from sqlalchemy import Column, Float, ForeignKey, Integer

from app.models.test import Test


class SprintTest(Test):
    """Prueba de velocidad en sprint con tiempos parciales y calculos derivados."""

    __tablename__ = "sprint_tests"

    id = Column(Integer, ForeignKey("tests.id"), primary_key=True)

    distance_meters = Column(Float, nullable=False)
    time_0_10_s = Column(Float, nullable=False)
    time_0_30_s = Column(Float, nullable=False)

    # Polimorfismo
    __mapper_args__ = {
        "polymorphic_identity": "sprint_test",
    }

    # Propiedades calculadas
    @property
    def time_10_30_s(self) -> float:
        """Tiempo del segmento 10-30 metros (calculado)"""
        if self.time_0_30_s and self.time_0_10_s:
            return self.time_0_30_s - self.time_0_10_s
        return None

    @property
    def avg_speed_ms(self) -> float:
        """Velocidad promedio en m/s (calculada)"""
        if self.distance_meters and self.time_0_30_s and self.time_0_30_s > 0:
            return self.distance_meters / self.time_0_30_s
        return None

    @property
    def estimated_max_speed(self) -> float:
        """Velocidad máxima estimada en m/s (calculada)"""
        if self.avg_speed_ms:
            return self.avg_speed_ms * 1.15  # Factor estimativo
        return None

    def __repr__(self):
        return (
            f"<SprintTest id={self.id} "
            f"distance={self.distance_meters}m "
            f"time_0_10={self.time_0_10_s}s "
            f"time_0_30={self.time_0_30_s}s>"
        )
