"""
Router para gestionar inscripciones de deportistas de la comunidad universitaria UNL.

Contiene endpoints para:
- Registro de nuevos deportistas (POST /inscription/deportista)
- Validación de datos institucionales
- Auditoría de operaciones
"""

from app.controllers.athlete_controller import AthleteController
from app.core.database import get_db
from app.schemas.athlete_schema import (
    AthleteInscriptionDTO, 
    AthleteInscriptionResponseDTO
)
from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inscription", tags=["Inscription"])
athlete_controller = AthleteController()


@router.post(
    "/deportista",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar deportista UNL",
    description="Registra un nuevo deportista perteneciente a la comunidad universitaria (Estudiante, Docente, Administrativo, Trabajador)"
)
async def register_athlete(
    inscription_data: AthleteInscriptionDTO,
    db: Session = Depends(get_db)
):
    """
    Endpoint para inscripción de deportistas de la comunidad UNL.
    
    **Validaciones:**
    - DNI único en el sistema
    - Email institucional único y válido
    - Rol universitario válido (STUDENT, TEACHER, ADMIN, WORKER)
    - Datos personales sanitizados (prevención de XSS/SQLi)
    - Datos físicos en rango válido
    
    **Response 201 Created:**
    - athlete_id: ID del deportista creado
    - statistic_id: ID del registro de estadísticas inicializado
    
    **Response 409 Conflict:**
    - DNI o email ya existen en el sistema
    
    **Response 422 Unprocessable Entity:**
    - Datos inválidos según reglas de negocio
    - Rol universitario no válido
    
    **Ejemplo de request:**
    ```json
    {
        "first_name": "Juan",
        "last_name": "Pérez",
        "dni": "12345678",
        "phone": "3424123456",
        "birth_date": "1998-05-15",
        "institutional_email": "juan.perez@unl.edu.ar",
        "university_role": "STUDENT",
        "weight": "75.5",
        "height": "180"
    }
    ```
    """
    try:
        # Invocar lógica de negocio del controlador
        result = athlete_controller.register_athlete_unl(db, inscription_data)
        
        # Auditoría: registrar éxito de la operación
        logger.info(
            f"Inscripción exitosa - Deportista ID: {result.athlete_id}, "
            f"Email: {result.institutional_email}"
        )
        
        # Retornar respuesta exitosa
        return ResponseSchema(
            status="success",
            message="Deportista registrado exitosamente",
            data={
                "athlete_id": result.athlete_id,
                "statistic_id": result.statistic_id,
                "first_name": result.first_name,
                "last_name": result.last_name,
                "institutional_email": result.institutional_email
            }
        )
    
    except AppException as app_exc:
        # Auditoría: registrar fallo con detalles
        logger.warning(
            f"Inscripción rechazada - Error: {app_exc.message} "
            f"(Status: {app_exc.status_code})"
        )
        
        # Retornar respuesta de error con status code apropiado
        return ResponseSchema(
            status="error",
            message=app_exc.message,
            data=None
        )
    
    except Exception as exc:
        # Auditoría: registrar error inesperado
        logger.error(
            f"Error inesperado en inscripción: {str(exc)}",
            exc_info=True
        )
        
        # Retornar respuesta de error genérica
        return ResponseSchema(
            status="error",
            message="Error al procesar la inscripción. Intente más tarde.",
            data=None
        )
