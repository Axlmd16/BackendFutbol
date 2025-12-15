from app.dao.athlete_dao import AthleteDAO
from app.dao.representative_dao import RepresentativeDAO
from app.schemas.athlete_schema import MinorAthleteCreateSchema, MinorAthleteResponseSchema
from app.utils.exceptions import AlreadyExistsException, ValidationException, DatabaseException
from sqlalchemy.orm import Session
from datetime import date
import logging

logger = logging.getLogger(__name__)


class AthleteController:
    """
    Controlador de deportistas.
    
    Gestiona la lógica de negocio para registro y administración
    de atletas, incluyendo validaciones especiales para menores de edad.
    """
    
    def __init__(self):
        self.athlete_dao = AthleteDAO()
        self.representative_dao = RepresentativeDAO()
    
    def register_minor_athlete(
        self, 
        db: Session, 
        minor_data: MinorAthleteCreateSchema
    ) -> MinorAthleteResponseSchema:
        """
        Registra un deportista menor de edad junto con su representante legal.
        
        Validaciones de seguridad y negocio (OWASP):
        1. Verifica que el menor sea efectivamente < 18 años
        2. Valida autorización parental obligatoria
        3. Verifica unicidad de DNI del menor y representante
        4. Sanitiza todas las entradas (realizado en schemas)
        5. Maneja transacciones atómicas
        
        Args:
            db: Sesión de base de datos
            minor_data: Datos validados del menor y representante
            
        Returns:
            MinorAthleteResponseSchema con datos del atleta y representante creados
            
        Raises:
            ValidationException: Si las validaciones de negocio fallan
            AlreadyExistsException: Si el DNI ya existe
            DatabaseException: Si ocurre un error en la persistencia
        """
        try:
            # VALIDACIÓN 1: Verificar que sea menor de 18 años (ya validado en schema)
            today = date.today()
            age = today.year - minor_data.birth_date.year - (
                (today.month, today.day) < (minor_data.birth_date.month, minor_data.birth_date.day)
            )
            
            if age >= 18:
                logger.warning(f"Intento de registro de mayor de edad como menor: {minor_data.dni}")
                raise ValidationException(
                    "El deportista debe ser menor de 18 años para este tipo de registro"
                )
            
            # VALIDACIÓN 2: Verificar autorización parental (crítico)
            if not minor_data.parental_authorization:
                logger.warning(f"Intento de registro sin autorización parental: {minor_data.dni}")
                raise ValidationException(
                    "Se requiere autorización parental explícita para registrar menores de edad. "
                    "Por favor, asegúrese de obtener el consentimiento firmado del tutor legal."
                )
            
            # VALIDACIÓN 3: Verificar unicidad del DNI del menor
            existing_athlete = self.athlete_dao.get_by_dni(db, minor_data.dni)
            if existing_athlete:
                logger.warning(f"Intento de registro duplicado de menor con DNI: {minor_data.dni}")
                raise AlreadyExistsException(
                    f"Ya existe un deportista registrado con el DNI: {minor_data.dni}"
                )
            
            # VALIDACIÓN 4: Verificar unicidad del DNI del representante
            existing_representative = self.representative_dao.get_by_dni(
                db, 
                minor_data.representative.dni
            )
            
            # Si el representante no existe, crearlo
            if not existing_representative:
                logger.info(f"Creando nuevo representante con DNI: {minor_data.representative.dni}")
                representative_data = {
                    "first_name": minor_data.representative.first_name,
                    "last_name": minor_data.representative.last_name,
                    "dni": minor_data.representative.dni,
                    "address": minor_data.representative.address,
                    "phone": minor_data.representative.phone,
                    "email": minor_data.representative.email
                }
                representative = self.representative_dao.create(db, representative_data)
            else:
                logger.info(f"Usando representante existente con DNI: {minor_data.representative.dni}")
                representative = existing_representative
            
            # PERSISTENCIA: Crear el deportista menor vinculado al representante
            logger.info(f"Registrando deportista menor: {minor_data.dni}")
            athlete_data = {
                "first_name": minor_data.first_name,
                "last_name": minor_data.last_name,
                "dni": minor_data.dni,
                "birth_date": minor_data.birth_date,
                "sex": minor_data.sex,
                "type_athlete": "MINOR",  # Tipo automático para menores
                "representative_id": representative.id,
                "parental_authorization": "SI"  # Confirmado explícitamente
            }
            
            athlete = self.athlete_dao.create(db, athlete_data)
            
            # AUDITORÍA: Registrar la acción en logs
            logger.info(
                f"✅ Deportista menor registrado exitosamente - "
                f"Atleta ID: {athlete.id}, DNI: {athlete.dni}, "
                f"Representante ID: {representative.id}, DNI: {representative.dni}, "
                f"Edad: {age} años"
            )
            
            # Construir respuesta completa
            from app.schemas.athlete_schema import (
                AthleteResponseSchema, 
                RepresentativeResponseSchema
            )
            
            athlete_response = AthleteResponseSchema.model_validate(athlete)
            representative_response = RepresentativeResponseSchema.model_validate(representative)
            
            return MinorAthleteResponseSchema(
                athlete=athlete_response,
                representative=representative_response
            )
            
        except (ValidationException, AlreadyExistsException) as e:
            # Re-lanzar excepciones de negocio
            raise e
        except Exception as e:
            # Capturar cualquier otro error y convertirlo en DatabaseException
            logger.error(f"Error inesperado al registrar menor de edad: {str(e)}")
            db.rollback()
            raise DatabaseException(
                "Ocurrió un error al procesar el registro del deportista menor. "
                "Por favor, intente nuevamente o contacte al administrador."
            )
