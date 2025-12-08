from app.dao.statistic_dao import StatisticDAO


class StatisticController:
    """Controlador de estadísticas de atletas."""

    def __init__(self):
        self.statistic_dao = StatisticDAO()
