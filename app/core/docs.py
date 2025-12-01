from typing import Dict, Any

def get_openapi_config() -> Dict[str, Any]:
    """Configuración personalizada de OpenAPI"""
    return {
        "title": "Backend Fútbol API",
        "version": "1.0.0",
        "description": """
        ## 🚀 API REST para gestión de fútbol
        
        Esta API proporciona endpoints para gestionar:
        - Usuarios y autenticación
        - Equipos y jugadores
        - Estadísticas y resultados
        
        ### Arquitectura
        - **Framework**: FastAPI
        - **Base de datos**: PostgreSQL
        - **ORM**: SQLAlchemy
        - **Patrón**: MVC con DAOs genéricos
        
        ### Autenticación
        Algunos endpoints requieren autenticación mediante JWT token.
        
        **Header requerido:**
```
        Authorization: Bearer <token>
```
        
        ### Respuestas
        Todas las respuestas siguen el formato:
```json
        {
            "status": "success",
            "message": "Descripción de la operación",
            "data": { }
        }
```
        """,
        "contact": {
            "name": "Equipo de Desarrollo",
            "email": "dev@backendfutbol.com"
        },
        "license_info": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    }

def get_tags_metadata() -> list[Dict[str, Any]]:
    """Metadata para agrupar endpoints"""
    return [
        {
            "name": "Users",
            "description": "Operaciones relacionadas con usuarios. Incluye registro, autenticación y gestión de perfiles."
        },
        {
            "name": "Health",
            "description": "Endpoints para verificar el estado de la API"
        }
    ]