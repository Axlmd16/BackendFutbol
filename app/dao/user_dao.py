from app.dao.base import BaseDAO
from app.models.user import User


class UserDAO(BaseDAO[User]):
    """DAO para gestión de usuarios del sistema."""

    def __init__(self) -> None:
        super().__init__(User)
