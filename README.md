# BackendFutbol API

API en FastAPI para gestionar evaluaciones, pruebas y estadísticas de atletas de fútbol.

## Stack rápido

-   Python + FastAPI
-   SQLAlchemy + Postgres
-   Pydantic Settings (.env) para configuración
-   uv para ejecutar/aislar entorno

## Config rápida

1. Crea un `.env` con tu base de datos Postgres:

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=backend_futbol
APP_PORT=8000
APP_HOST=0.0.0.0
DEBUG=true
JWT_SECRET=devsecret
```

2. Instala dependencias y corre el server:

```
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Puntos de entrada

-   `main.py`: crea la app, registra routers y dispara `Base.metadata.create_all()`.
-   `app/core/database.py`: engine y `SessionLocal` con helper `get_db` (dependencia para FastAPI).
-   `app/core/config.py`: variables de entorno via Pydantic Settings (`.env`).
-   `app/models`: modelos SQLAlchemy ya documentados en español.

## Uso del DAO genérico

El `BaseDAO` (`app/dao/base.py`) concentra CRUD, soft delete, búsqueda paginada y filtros dinámicos. Se instancia con el modelo SQLAlchemy que necesitas manejar.

Ejemplo mínimo en un servicio/endpoint:

```python
from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.dao.base import BaseDAO
from app.models.user import User

router = APIRouter()
user_dao = BaseDAO(User)

@router.get("/users")
def list_users(db = Depends(get_db)):
	return user_dao.get_all(db)

@router.post("/users")
def create_user(payload: dict, db = Depends(get_db)):
	return user_dao.create(db, payload)
```

## Documentación interactiva

-   Swagger UI: `http://localhost:8000/docs`
-   ReDoc: `http://localhost:8000/redoc`
-   Scalar: `http://localhost:8000/scalar`

Las tres rutas exponen el mismo OpenAPI; usa Scalar si quieres una experiencia moderna y rápida, o Swagger para probar endpoints rápidamente.
