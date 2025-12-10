from app.dao.user_dao import UserDAO


class UserController:
    """Controlador de usuarios del sistema."""

    def __init__(self) -> None:
        self.user_dao = UserDAO()
