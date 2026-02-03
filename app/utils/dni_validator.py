"""Utilidades para validación de DNI en entidades locales."""

from sqlalchemy.orm import Session

from app.utils.exceptions import AlreadyExistsException


def validate_dni_not_exists_locally(
    db: Session,
    dni: str,
    *,
    check_users: bool = True,
    check_athletes: bool = True,
    check_representatives: bool = True,
) -> None:
    """
    Valida que un DNI no exista ya en las entidades locales del sistema.

    Esta validación debe ejecutarse ANTES de intentar crear/validar en el
    microservicio de usuarios para dar mensajes de error más claros.

    Args:
        db: Sesión de base de datos
        dni: Número de documento a verificar
        check_users: Si validar en tabla de usuarios
        check_athletes: Si validar en tabla de atletas
        check_representatives: Si validar en tabla de representantes

    Raises:
        AlreadyExistsException: Si el DNI ya existe en alguna entidad
    """
    from app.dao.athlete_dao import AthleteDAO
    from app.dao.representative_dao import RepresentativeDAO
    from app.dao.user_dao import UserDAO

    # Verificar en usuarios
    if check_users:
        user_dao = UserDAO()
        if user_dao.get_by_field(db, "dni", dni, only_active=False):
            raise AlreadyExistsException(
                f"Ya existe un usuario con el DNI {dni} en el sistema"
            )

    # Verificar en atletas
    if check_athletes:
        athlete_dao = AthleteDAO()
        if athlete_dao.get_by_field(db, "dni", dni, only_active=False):
            raise AlreadyExistsException(
                f"Ya existe un deportista con el DNI {dni} en el sistema"
            )

    # Verificar en representantes
    if check_representatives:
        representative_dao = RepresentativeDAO()
        if representative_dao.get_by_field(db, "dni", dni, only_active=False):
            raise AlreadyExistsException(
                f"Ya existe un representante con el DNI {dni} en el sistema"
            )
