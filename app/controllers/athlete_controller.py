from app.dao.athlete_dao import AthleteDAO
from app.dao.statistic_dao import StatisticDAO
from app.schemas.athlete_schema import AthleteInscriptionDTO, AthleteInscriptionResponseDTO
from app.utils.exceptions import (
    ValidationException, 
    AlreadyExistsException, 
    DatabaseException
)
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class AthleteController:
    """
    Controlador de deportistas con lógica de negocio para inscripción
    y gestión de datos de atletas.
    """
    
    def __init__(self):
        self.athlete_dao = AthleteDAO()
        self.statistic_dao = StatisticDAO()
    
    def register_athlete_unl(
        self, 
        db: Session, 
        inscription_data: AthleteInscriptionDTO
    ) -> AthleteInscriptionResponseDTO:
        """
        Registra un nuevo deportista perteneciente a la comunidad UNL.
        
        Validaciones:
        1. Verifica que el DNI no exista en la BD
        2. Verifica que el email institucional no exista en la BD
        3. Valida que el rol universitario sea válido
        4. Crea la entidad Deportista
        5. Inicializa registro de Estadísticas
        
        Args:
            db: Sesión de base de datos
            inscription_data: DTO con datos del deportista
            
        Returns:
            AthleteInscriptionResponseDTO con IDs de deportista y estadísticas
            
        Raises:
            ValidationException: Si datos no cumplen reglas de negocio
            AlreadyExistsException: Si DNI o email ya existen
            DatabaseException: Si hay error en persistencia
        """
        try:
            # 1. Validar que el rol universitario sea válido (OWASP - validación de entrada)
            valid_roles = {"STUDENT", "TEACHER", "ADMIN", "WORKER"}
            if inscription_data.university_role.upper() not in valid_roles:
                logger.warning(
                    f"Intento de registro con rol inválido: {inscription_data.university_role}"
                )
                raise ValidationException(
                    f"Rol universitario inválido. Debe ser uno de: {', '.join(valid_roles)}"
                )
            
            # 2. Validar unicidad del DNI
            if self.athlete_dao.exists(db, "dni", inscription_data.dni):
                logger.warning(
                    f"Intento de registro con DNI duplicado: {inscription_data.dni}"
                )
                raise AlreadyExistsException(
                    "El DNI ya existe en el sistema. Verifique e intente nuevamente."
                )
            
            # 3. Validar unicidad del email institucional
            if self.athlete_dao.exists(
                db, 
                "institutional_email", 
                inscription_data.institutional_email
            ):
                logger.warning(
                    f"Intento de registro con email duplicado: {inscription_data.institutional_email}"
                )
                raise AlreadyExistsException(
                    "El email institucional ya existe en el sistema."
                )
            
            # 4. Crear entidad Deportista con datos sanitizados
            athlete_data = {
                "first_name": inscription_data.first_name,
                "last_name": inscription_data.last_name,
                "dni": inscription_data.dni,
                "phone": inscription_data.phone,
                "birth_date": inscription_data.birth_date,
                "institutional_email": inscription_data.institutional_email,
                "university_role": inscription_data.university_role.upper(),
                "weight": inscription_data.weight,
                "height": inscription_data.height,
                "type_athlete": "UNL"  # Tipo de deportista asignado automáticamente
            }
            
            athlete = self.athlete_dao.create(db, athlete_data)
            logger.info(
                f"Deportista registrado exitosamente: {athlete.id} - "
                f"{athlete.first_name} {athlete.last_name}"
            )
            
            # 5. Inicializar registro de Estadísticas con valores por defecto
            statistic_data = {
                "athlete_id": athlete.id,
                "speed": None,
                "stamina": None,
                "strength": None,
                "agility": None,
                "matches_played": 0,
                "goals": 0,
                "assists": 0,
                "yellow_cards": 0,
                "red_cards": 0
            }
            
            statistic = self.statistic_dao.create(db, statistic_data)
            logger.info(
                f"Estadísticas inicializadas para deportista {athlete.id}"
            )
            
            # Retornar respuesta exitosa
            return AthleteInscriptionResponseDTO(
                athlete_id=athlete.id,
                statistic_id=statistic.id,
                first_name=athlete.first_name,
                last_name=athlete.last_name,
                institutional_email=athlete.institutional_email,
                message="Deportista registrado exitosamente"
            )
            
        except (ValidationException, AlreadyExistsException):
            # Re-lanzar excepciones de negocio
            raise
        except DatabaseException:
            # Re-lanzar excepciones de BD
            raise
        except Exception as e:
            logger.error(f"Error inesperado en inscripción de deportista: {str(e)}")
            raise DatabaseException(
                "Error al registrar deportista. Intente nuevamente."
            )
