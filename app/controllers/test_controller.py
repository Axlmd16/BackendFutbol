from app.dao.test_dao import TestDAO


class TestController:
    """Controlador de pruebas base."""

    __test__ = False  # evitar que pytest lo tome como test

    def __init__(self):
        self.test_dao = TestDAO()
