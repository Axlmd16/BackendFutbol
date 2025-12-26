from app.dao.athlete_dao import AthleteDAO
from app.dao.statistic_dao import StatisticDAO
from app.schemas.athlete_schema import AthleteInscriptionDTO, AthleteInscriptionResponseDTO
from app.utils.exceptions import ValidationException, AlreadyExistsException, DatabaseException
from app.utils.security import validate_ec_dni
from sqlalchemy.orm import Session


class AthleteController:
    """Controlador de deportistas."""

    def __init__(self) -> None:
        self.athlete_dao = AthleteDAO()
        self.statistic_dao = StatisticDAO()

    def register_athlete_unl(self, db: Session, data: AthleteInscriptionDTO) -> AthleteInscriptionResponseDTO:
        dni = validate_ec_dni(data.dni)
        valid_roles = {"STUDENT", "TEACHER", "ADMIN", "WORKER"}
        role = data.university_role.upper()
        if role not in valid_roles:
            raise ValidationException(f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}")

        if self.athlete_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("El DNI ya existe en el sistema.")
        if self.athlete_dao.exists(db, "institutional_email", data.institutional_email):
            raise AlreadyExistsException("El email institucional ya existe en el sistema.")

        athlete = self.athlete_dao.create(db, {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "dni": dni,
            "phone": data.phone,
            "birth_date": data.birth_date,
            "institutional_email": data.institutional_email,
            "university_role": role,
            "weight": data.weight,
            "height": data.height,
            "type_athlete": "UNL",
        })

        statistic = self.statistic_dao.create(db, {
            "athlete_id": athlete.id,
            "matches_played": 0,
            "goals": 0,
            "assists": 0,
            "yellow_cards": 0,
            "red_cards": 0,
        })

        return AthleteInscriptionResponseDTO(
            athlete_id=athlete.id,
            statistic_id=statistic.id,
            first_name=athlete.first_name,
            last_name=athlete.last_name,
            institutional_email=athlete.institutional_email,
        )
