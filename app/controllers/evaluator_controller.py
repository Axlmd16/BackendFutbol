from app.dao.evaluator_dao import EvaluatorDAO


class EvaluatorController:
    """Controlador de evaluadores."""

    def __init__(self):
        self.evaluator_dao = EvaluatorDAO()
