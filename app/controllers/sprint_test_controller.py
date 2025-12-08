from app.dao.sprint_test_dao import SprintTestDAO


class SprintTestController:
    """Controlador de pruebas de sprint."""

    def __init__(self):
        self.sprint_test_dao = SprintTestDAO()
