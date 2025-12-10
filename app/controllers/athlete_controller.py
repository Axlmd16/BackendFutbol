from app.dao.athlete_dao import AthleteDAO
from app.dao.statistic_dao import StatisticDAO
from app.schemas.athlete_schema import AthleteInscriptionDTO, AthleteInscriptionResponseDTO
from app.utils.exceptions import ValidationException, AlreadyExistsException, DatabaseException
from sqlalchemy.orm import Session


class AthleteController:
    """Controlador de deportistas."""

    def __init__(self):
        self.athlete_dao = AthleteDAO()
        self.statistic_dao = StatisticDAO()
    
    def register_athlete_unl(self, db: Session, inscription_data: AthleteInscriptionDTO) -> AthleteInscriptionResponseDTO:
        """Registra un nuevo deportista de la comunidad UNL."""
        try:
            # Validar rol universitario
            valid_roles = {"STUDENT", "TEACHER", "ADMIN", "WORKER"}
            if inscription_data.university_role.upper() not in valid_roles:
                raise ValidationException(f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}")

            # Validar unicidad de DNI
            if self.athlete_dao.exists(db, "dni", inscription_data.dni):
                raise AlreadyExistsException("El DNI ya existe en el sistema.")

            # Validar unicidad de email
            if self.athlete_dao.exists(db, "institutional_email", inscription_data.institutional_email):
                raise AlreadyExistsException("El email institucional ya existe en el sistema.")

            # Crear deportista
            athlete = self.athlete_dao.create(db, {
                "first_name": inscription_data.first_name,
                "last_name": inscription_data.last_name,
                "dni": inscription_data.dni,
                "phone": inscription_data.phone,
                "birth_date": inscription_data.birth_date,
                "institutional_email": inscription_data.institutional_email,
                "university_role": inscription_data.university_role.upper(),
                "weight": inscription_data.weight,
                "height": inscription_data.height,
                "type_athlete": "UNL"
            })

            # Crear estadísticas
            statistic = self.statistic_dao.create(db, {
                "athlete_id": athlete.id,
                "matches_played": 0,
                "goals": 0,
                "assists": 0,
                "yellow_cards": 0,
                "red_cards": 0
            })

            return AthleteInscriptionResponseDTO(
                athlete_id=athlete.id,
                statistic_id=statistic.id,
                first_name=athlete.first_name,
                last_name=athlete.last_name,
                institutional_email=athlete.institutional_email
            )
        except (ValidationException, AlreadyExistsException):
            raise
        except Exception as e:
            raise DatabaseException(f"Error en inscripción: {str(e)}")
