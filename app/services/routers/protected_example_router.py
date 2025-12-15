"""
EJEMPLO: Router protegido con autenticación JWT.

Este archivo muestra cómo proteger endpoints usando el sistema de seguridad.
Puedes copiar estos patrones a tus routers existentes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user, CurrentUser
from app.schemas.response import ResponseSchema
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/protected-example", tags=["Ejemplos Protegidos"])


# EJEMPLO 1: Endpoint con autenticación básica
@router.get(
    "/basic-protected",
    response_model=ResponseSchema,
    summary="Endpoint con autenticación básica",
    description="Solo usuarios autenticados pueden acceder"
)
async def basic_protected_endpoint(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Endpoint protegido que requiere token válido.
    
    Headers requeridos:
        Authorization: Bearer <token>
    """
    return ResponseSchema(
        status="success",
        message=f"Bienvenido {current_user.email}",
        data={
            "user_id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "external_id": current_user.external_id
        }
    )


# EJEMPLO 2: Endpoint que requiere usuario activo
@router.post(
    "/active-users-only",
    response_model=ResponseSchema,
    summary="Solo usuarios activos",
    description="Requiere que el usuario esté activo en el sistema"
)
async def active_users_endpoint(
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint que verifica que el usuario esté activo.
    
    Headers requeridos:
        Authorization: Bearer <token>
    """
    return ResponseSchema(
        status="success",
        message="Usuario activo verificado",
        data={"email": current_user.email, "role": current_user.role}
    )


# EJEMPLO 3: Endpoint con información del usuario para auditoría
@router.post(
    "/with-audit",
    response_model=ResponseSchema,
    summary="Endpoint con auditoría de usuario",
    description="Registra quién realizó la acción"
)
async def endpoint_with_audit(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ejemplo de endpoint que registra quién realizó la acción.
    
    Útil para:
    - Registros de auditoría
    - Tracking de cambios
    - Compliance y trazabilidad
    """
    # Aquí puedes usar current_user.email o current_user.id
    # para registrar quién hizo la acción
    logger.info(f"Acción realizada por: {current_user.email} (ID: {current_user.id})")
    
    return ResponseSchema(
        status="success",
        message="Acción registrada con auditoría",
        data={
            "performed_by": current_user.email,
            "user_role": current_user.role,
            "timestamp": "2025-12-14T00:00:00Z"
        }
    )


# EJEMPLO 4: Endpoint con validación de rol (solo administradores)
@router.delete(
    "/admin-only",
    response_model=ResponseSchema,
    summary="Solo administradores",
    description="Endpoint restringido a usuarios con rol ADMIN"
)
async def admin_only_endpoint(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Endpoint que solo puede ser accedido por administradores.
    
    Verifica manualmente el rol del usuario.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo administradores pueden realizar esta acción."
        )
    
    return ResponseSchema(
        status="success",
        message="Acción de administrador ejecutada",
        data={"admin_user": current_user.email}
    )
