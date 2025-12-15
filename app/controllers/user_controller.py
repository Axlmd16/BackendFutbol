# app/controllers/user_controller.py
import logging
from sqlalchemy.orm import Session

from app.dao.account_dao import AccountDAO
from app.dao.user_dao import UserDAO
from app.models.account import Account
from app.models.enums.rol import Role
from app.schemas.user_schema import AdminCreateUserRequest, AdminCreateUserResponse
from app.utils.exceptions import (
    AlreadyExistsException,
    UnauthorizedException,
    ValidationException,
    DatabaseException,
)
from app.utils.person_creator import create_person_with_account_in_ms
from app.utils.security import validate_ec_dni  # ← IMPORTAR

logger = logging.getLogger(__name__)


class UserController:
    """Controlador de usuarios del sistema (club)."""

    def __init__(self) -> None:
        self.user_dao = UserDAO()
        self.account_dao = AccountDAO()


    async def admin_create_user(
        self,
        db: Session,
        payload: AdminCreateUserRequest,
        requester_account_id: int | None = None,
    ) -> AdminCreateUserResponse:
        """Crea un admin/entrenador en el MS de usuarios y lo enlaza al club."""

        # TODO: habilitar validación de admin despues con auth
        # if requester_account_id is not None:
        #     self._ensure_requester_is_admin(db, requester_account_id)

        # Mapear string al Rol
        role_str = payload.role.strip().lower()
        if role_str in ("administrador", "administrator", "admin"):
            role_enum = Role.ADMINISTRATOR
        elif role_str in ("entrenador", "coach"):
            role_enum = Role.COACH
        else:
            raise ValidationException("Rol inválido. Use 'administrador' o 'entrenador'")

        dni = validate_ec_dni(payload.dni)
        
        if self.user_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("Ya existe un usuario con ese DNI en el club")

        # Crear persona + cuenta en el MS usando la función de utils
        person_data = await create_person_with_account_in_ms(
            first_name=payload.first_name,
            last_name=payload.last_name,
            dni=payload.dni,
            email=payload.email,
            password=payload.password,
            type_identification=payload.type_identification,
            type_stament=payload.type_stament,
            direction=payload.direction,
            phone=payload.phone,
        )

        # Extraer datos retornados
        external_person_id = person_data["external_person_id"]
        external_account_id = person_data["external_account_id"]
        full_name = person_data["full_name"]
        email = person_data["email"]
        dni = person_data["dni"]

        # Guardar el enlace local en el club
        try:
            new_user = self.user_dao.create(db, {
                "external_person_id": external_person_id,
                "full_name": full_name,
                "dni": dni,
            })

            new_account = self.account_dao.create(db, {
                "external_account_id": external_account_id,
                "role": role_enum,
                "user_id": new_user.id,
            })
        except DatabaseException as e:
            logger.error(f"Error al crear registros locales de usuario/cuenta: {e}")
            raise

        # TODO: enviar email de bienvenida con credenciales

        return AdminCreateUserResponse(
            user_id=new_user.id,
            account_id=new_account.id,
            external_person_id=external_person_id,
            external_account_id=external_account_id,
            full_name=full_name,
            email=email,
            role=new_account.role.value,
        )
