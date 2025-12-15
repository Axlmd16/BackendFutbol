"""
Módulo de seguridad y autenticación.

Proporciona funcionalidad de autenticación JWT para endpoints protegidos.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


security = HTTPBearer()


class CurrentUser(BaseModel):
    """
    Modelo de usuario autenticado extraído del token JWT.
    
    Attributes:
        id: ID único del usuario
        email: Email del usuario
        role: Rol del usuario (ADMIN, USER, etc.)
        external_id: ID en sistema externo (opcional)
        is_active: Si el usuario está activo
    """
    id: int
    email: str
    role: str
    external_id: Optional[str] = None
    is_active: bool = True


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependencia para obtener el usuario autenticado actual.
    
    Extrae y valida el token JWT del header Authorization.
    
    Args:
        credentials: Credenciales HTTP Bearer con el token JWT
        
    Returns:
        CurrentUser: Información del usuario autenticado
        
    Raises:
        HTTPException: 401 si el token es inválido o está expirado
        
    Note:
        Esta es una implementación básica. Para producción, se debe:
        - Validar firma del token con clave secreta
        - Verificar expiración del token
        - Validar issuer y audience
        - Integrar con el servicio de autenticación Spring Boot
    """
    token = credentials.credentials
    
    # NOTA: Esta es una implementación simplificada para desarrollo
    # En producción, aquí se debe validar el token JWT con PyJWT
    # y extraer los claims del usuario desde el payload
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implementar validación real del token JWT
    # Ejemplo (requiere PyJWT):
    # try:
    #     payload = jwt.decode(
    #         token,
    #         settings.OTHERS_KEY,
    #         algorithms=["HS256", "HS512"]
    #     )
    #     return CurrentUser(
    #         id=payload.get("id"),
    #         email=payload.get("email"),
    #         role=payload.get("role"),
    #         external_id=payload.get("external_id"),
    #         is_active=payload.get("is_active", True)
    #     )
    # except jwt.ExpiredSignatureError:
    #     raise HTTPException(401, "Token expirado")
    # except jwt.InvalidTokenError:
    #     raise HTTPException(401, "Token inválido")
    
    # Implementación temporal para desarrollo (ELIMINAR EN PRODUCCIÓN)
    return CurrentUser(
        id=1,
        email="dev@test.com",
        role="ADMIN",
        is_active=True
    )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependencia que verifica además que el usuario esté activo.
    
    Args:
        current_user: Usuario autenticado
        
    Returns:
        CurrentUser: Usuario autenticado y activo
        
    Raises:
        HTTPException: 403 si el usuario está inactivo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user
