"""Router para inscripciones de deportistas en la escuela de fútbol."""

from app.controllers.athlete_controller import AthleteController
from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.schemas.athlete_schema import MinorAthleteCreateSchema, MinorAthleteResponseSchema
from app.schemas.response import ResponseSchema
from app.utils.exceptions import (
    AlreadyExistsException, 
    ValidationException, 
    DatabaseException,
    AppException
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inscription/escuela-futbol", tags=["Inscripciones"])
athlete_controller = AthleteController()


@router.post(
    "/deportista-menor",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar deportista menor de edad",
    description="""
    Registra un nuevo deportista menor de 18 años junto con su representante legal.
    
    **Validaciones de seguridad implementadas (OWASP):**
    - ✅ Verificación de edad (debe ser < 18 años)
    - ✅ Autorización parental obligatoria
    - ✅ Validación de unicidad de DNI (menor y representante)
    - ✅ Sanitización de entradas (prevención de inyección SQL/XSS)
    - ✅ Validación de formato de email, teléfono y DNI
    
    **Requisitos legales:**
    - El campo `parental_authorization` debe ser `true`
    - Se debe proporcionar información completa del representante legal
    - El menor debe tener entre 5 y 17 años
    
    **Proceso:**
    1. Valida que el deportista sea menor de edad
    2. Valida que exista autorización parental explícita
    3. Verifica que no exista duplicado del DNI del menor
    4. Crea o vincula al representante legal
    5. Registra al deportista con tipo "MINOR"
    6. Registra la acción en auditoría
    """,
    responses={
        201: {
            "description": "Deportista menor registrado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Deportista menor de edad registrado exitosamente",
                        "data": {
                            "athlete": {
                                "id": 1,
                                "first_name": "Juan Carlos",
                                "last_name": "Pérez López",
                                "dni": "12345678",
                                "birth_date": "2010-05-15",
                                "sex": "M",
                                "type_athlete": "MINOR",
                                "representative_id": 1,
                                "parental_authorization": "SI",
                                "created_at": "2025-12-08T10:30:00",
                                "is_active": True
                            },
                            "representative": {
                                "id": 1,
                                "first_name": "María Elena",
                                "last_name": "López García",
                                "dni": "87654321",
                                "address": "Av. Principal 123, Ciudad",
                                "phone": "+593 99 123 4567",
                                "email": "maria.lopez@email.com",
                                "created_at": "2025-12-08T10:30:00",
                                "is_active": True
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Error de validación",
            "content": {
                "application/json": {
                    "examples": {
                        "no_autorizacion": {
                            "summary": "Sin autorización parental",
                            "value": {
                                "status": "error",
                                "message": "Se requiere autorización parental explícita para registrar menores de edad",
                                "data": None
                            }
                        },
                        "mayor_edad": {
                            "summary": "No es menor de edad",
                            "value": {
                                "status": "error",
                                "message": "El deportista debe ser menor de 18 años para este tipo de registro",
                                "data": None
                            }
                        }
                    }
                }
            }
        },
        409: {
            "description": "DNI duplicado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Ya existe un deportista registrado con el DNI: 12345678",
                        "data": None
                    }
                }
            }
        },
        500: {
            "description": "Error del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Error al procesar el registro del deportista menor",
                        "data": None
                    }
                }
            }
        }
    }
)
async def register_minor_athlete(
    minor_data: MinorAthleteCreateSchema,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para registrar un deportista menor de edad.
    
    **PROTECCIÓN:** Requiere autenticación con token JWT válido.
    
    Implementa todas las validaciones de seguridad y negocio requeridas
    según estándares OWASP y requisitos legales para menores.
    
    Headers requeridos:
        Authorization: Bearer <token>
    
    Args:
        minor_data: Datos validados del menor y su representante legal
        current_user: Usuario autenticado (inyectado por dependencia)
        db: Sesión de base de datos (inyectada)
        
    Returns:
        ResponseSchema con datos del atleta y representante creados
    """
    try:
        # Registrar quién realizó la inscripción (auditoría)
        logger.info(
            f"Iniciando registro de menor por usuario: {current_user.email} "
            f"(ID: {current_user.id}, Role: {current_user.role})"
        )
        
        # Llamar al controlador que contiene toda la lógica de negocio
        result = athlete_controller.register_minor_athlete(db, minor_data)
        
        logger.info(
            f"✅ Endpoint exitoso - Menor registrado: {minor_data.dni} "
            f"por usuario: {current_user.email}"
        )
        
        return ResponseSchema(
            status="success",
            message="Deportista menor de edad registrado exitosamente. "
                   "El representante legal ha sido vinculado correctamente.",
            data=result.model_dump()
        )
        
    except ValidationException as e:
        logger.warning(f"⚠️ Error de validación: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=ResponseSchema(
                status="error",
                message=e.message,
                data=None
            ).model_dump()
        )
    
    except AlreadyExistsException as e:
        logger.warning(f"⚠️ DNI duplicado: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=ResponseSchema(
                status="error",
                message=e.message,
                data=None
            ).model_dump()
        )
    
    except DatabaseException as e:
        logger.error(f"❌ Error de base de datos: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=ResponseSchema(
                status="error",
                message=e.message,
                data=None
            ).model_dump()
        )
    
    except AppException as e:
        logger.error(f"❌ Error de aplicación: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=ResponseSchema(
                status="error",
                message=e.message,
                data=None
            ).model_dump()
        )
    
    except Exception as e:
        logger.error(f"❌ Error inesperado en endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ResponseSchema(
                status="error",
                message="Error interno del servidor. Por favor, contacte al administrador.",
                data=None
            ).model_dump()
        )
