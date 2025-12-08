from app.dao.technical_assessment_dao import TechnicalAssessmentDAO


class TechnicalAssessmentController:
    """Controlador de evaluaciones técnicas."""

    def __init__(self):
        self.technical_assessment_dao = TechnicalAssessmentDAO()
