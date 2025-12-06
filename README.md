# Backend Fútbol API ⚽

API REST desarrollada con FastAPI para la gestión de datos de fútbol, incluyendo usuarios, atletas, evaluaciones físicas y estadísticas.

## 📋 Stack Tecnológico

-   **Python 3.13+** con FastAPI
-   **SQLAlchemy** + PostgreSQL
-   **Pydantic Settings** para gestión de configuración (.env)
-   **uv** para gestión de dependencias y entorno aislado

## 🚀 Configuración Rápida

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd backendfutbol
```

### 2. Crear y activar entorno virtual

**En Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**En macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

El proyecto utiliza `pyproject.toml` para manejar las dependencias.

```bash
# Opción estándar con pip
pip install -e .

# Opción con uv (recomendado, más rápido)
uv sync
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con la siguiente configuración:

```env
# Configuración de Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_password
DB_NAME=backendfutbol_db

# Configuración de la App
APP_PORT=8000
APP_HOST=0.0.0.0
DEBUG=true

# Seguridad
JWT_SECRET=secreto_super_seguro_para_desarrollo_123
TOKEN_EXPIRES=3600
```

> **Nota:** La base de datos debe estar creada previamente en PostgreSQL. Las tablas se crearán automáticamente al iniciar la aplicación.

## ▶️ Ejecutar la aplicación

Para iniciar el servidor de desarrollo con recarga automática:

```bash
# Opción 1: Usando el punto de entrada principal
python main.py

# Opción 2: Usando uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opción 3: Usando uv (recomendado)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentación Interactiva

Una vez iniciado el servidor, accede a la documentación en:

-   **Scalar Docs** (Recomendado): http://localhost:8000/scalar
-   **Swagger UI**: http://localhost:8000/docs
-   **ReDoc**: http://localhost:8000/redoc

Las tres rutas exponen el mismo esquema OpenAPI; usa Scalar para una experiencia moderna y rápida, o Swagger para probar endpoints interactivamente.

## 📂 Estructura del Proyecto

```
backendfutbol/
├── .github/            # Workflows de GitHub Actions
├── app/
│   ├── core/           # Configuración, DB, Seguridad
│   │   ├── config.py   # Variables de entorno via Pydantic Settings
│   │   └── database.py # Engine, SessionLocal y helper get_db
│   ├── dao/            # Data Access Objects (CRUD Genérico)
│   │   └── base.py     # BaseDAO con operaciones CRUD, soft delete y filtros
│   ├── models/         # Modelos SQLAlchemy (Tablas)
│   ├── schemas/        # Schemas Pydantic (Validación)
│   ├── services/       # Lógica de negocio y Routers
│   └── utils/          # Excepciones y utilidades
├── main.py             # Punto de entrada (registra routers, crea tablas)
├── pyproject.toml      # Definición de dependencias
└── uv.lock             # Bloqueo de versiones
```

## 🔧 Arquitectura y Componentes

### Puntos de Entrada Principales

-   **`main.py`**: Crea la aplicación FastAPI, registra routers y ejecuta `Base.metadata.create_all()` para crear las tablas.
-   **`app/core/database.py`**: Configura el engine SQLAlchemy y proporciona `SessionLocal` con el helper `get_db` como dependencia para FastAPI.
-   **`app/core/config.py`**: Maneja las variables de entorno usando Pydantic Settings, cargando la configuración desde el archivo `.env`.
-   **`app/models`**: Contiene los modelos SQLAlchemy documentados en español que representan las tablas de la base de datos.

### BaseDAO - CRUD Genérico

El `BaseDAO` (`app/dao/base.py`) proporciona operaciones CRUD completas, soft delete, búsqueda paginada y filtros dinámicos. Se instancia con el modelo SQLAlchemy que necesitas manejar.

**Ejemplo de uso en un servicio/endpoint:**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dao.base import BaseDAO
from app.models.user import User

router = APIRouter()
user_dao = BaseDAO(User)

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    return user_dao.get_all(db)

@router.post("/users")
def create_user(payload: dict, db: Session = Depends(get_db)):
    return user_dao.create(db, payload)

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_dao.get_by_id(db, user_id)

@router.put("/users/{user_id}")
def update_user(user_id: int, payload: dict, db: Session = Depends(get_db)):
    return user_dao.update(db, user_id, payload)

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return user_dao.delete(db, user_id)  # Soft delete
```

## 🌳 Flujo de Trabajo Git (Gitflow Personalizado)

Este proyecto sigue una arquitectura de ramas estricta para mantener la calidad del código y facilitar el trabajo en equipo.

### Estructura de Ramas

| Rama          | Entorno      | Descripción                                                        |
| ------------- | ------------ | ------------------------------------------------------------------ |
| `main`        | Producción   | Código estable y desplegable. **No hacer commits directos.**       |
| `staging`     | QA / Pruebas | Entorno para testing antes de salir a producción.                  |
| `development` | Desarrollo   | Rama principal de integración. Todo el trabajo nace y vuelve aquí. |

### Flujo de Trabajo (Paso a Paso)

1. **Sincronízate**: Asegúrate de estar en `development` y tener los últimos cambios:

    ```bash
    git checkout development
    git pull origin development
    ```

2. **Crea tu Feature**: Crea una rama para tu tarea desde `development`:

    ```bash
    git checkout -b feature/nombre-descriptivo
    ```

    - **Nomenclatura**: `feature/nombre-tarea` (ej. `feature/login-auth`)
    - Si usas GitKraken: Usa el botón "Start Feature"

3. **Desarrolla**: Haz tus commits en tu rama `feature/...` con mensajes descriptivos.

4. **Finaliza**:
    - Haz push de tu rama:
        ```bash
        git push origin feature/nombre-descriptivo
        ```
    - Abre un **Pull Request** hacia `development`
    - Una vez aprobado y fusionado, elimina tu rama local

### ⚠️ Reglas de Oro

-   ❌ **Nunca hagas commit directo a `main`**
-   ✅ Siempre trabaja desde ramas `feature/`
-   ✅ Todos los cambios deben pasar por Pull Request
-   ✅ Si arreglas un bug en `release` o `staging`, asegúrate de hacer **Merge Down** hacia `development` para no perder el arreglo

## 🤝 Contribución

1. Asegúrate de seguir el flujo de trabajo Git descrito arriba
2. Escribe código limpio y bien documentado
3. Usa los schemas de Pydantic para validación de datos
4. Aprovecha el `BaseDAO` para operaciones CRUD estándar
5. Añade tests para nuevas funcionalidades

## 📝 Notas Adicionales

-   Los modelos SQLAlchemy están documentados en español para facilitar la comprensión
-   El `BaseDAO` soporta soft delete por defecto
-   La aplicación usa Pydantic Settings para una gestión robusta de configuración
-   Las tablas se crean automáticamente al iniciar la aplicación (no requiere migraciones manuales en desarrollo)

---
