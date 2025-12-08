from app.dao.test_dao import TestDAO


class TestController:
    """Controlador de pruebas base."""

    def __init__(self):
        self.test_dao = TestDAO()
