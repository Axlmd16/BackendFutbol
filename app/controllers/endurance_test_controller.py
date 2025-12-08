from app.dao.endurance_test_dao import EnduranceTestDAO


class EnduranceTestController:
    """Controlador de pruebas de resistencia."""

    def __init__(self):
        self.endurance_test_dao = EnduranceTestDAO()
