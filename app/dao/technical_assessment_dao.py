from app.dao.base import BaseDAO
from app.models.technical_assessment import TechnicalAssessment


class TechnicalAssessmentDAO(BaseDAO[TechnicalAssessment]):
    """DAO específico para evaluaciones técnicas."""

    def __init__(self):
        super().__init__(TechnicalAssessment)
