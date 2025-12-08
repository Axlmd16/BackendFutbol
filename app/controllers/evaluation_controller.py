from app.dao.evaluation_dao import EvaluationDAO


class EvaluationController:
    """Controlador de evaluaciones."""

    def __init__(self):
        self.evaluation_dao = EvaluationDAO()
