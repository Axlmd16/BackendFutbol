# Kallpa UNL - Backend API ⚽

Sistema de gestión deportiva desarrollado con FastAPI para la Universidad Nacional de Loja. Permite administrar usuarios, atletas, evaluaciones físicas, asistencia y estadísticas del Club de Fútbol Kallpa UNL.

## 📋 Stack Tecnológico

| Componente                 | Tecnología              |
| -------------------------- | ----------------------- |
| **Backend**                | Python 3.11+ / FastAPI  |
| **Base de Datos**          | PostgreSQL              |
| **ORM**                    | SQLAlchemy 2.0          |
| **Validación**             | Pydantic v2             |
| **Autenticación**          | JWT (python-jose)       |
| **Gestor de dependencias** | uv                      |
| **Linter/Formatter**       | Ruff                    |
| **Tests**                  | pytest + pytest-asyncio |
| **CI/CD**                  | GitHub Actions          |

---

## 🏗️ Arquitectura del Proyecto

```
BackendFutbol/
├── .github/workflows/        # Pipelines CI/CD
│   ├── fastapi-ci.yml        # CI para PRs a development
│   ├── staging-ci.yml        # CI para PRs a staging
│   └── production-ci.yml     # CI para PRs a main (producción)
│
├── app/
│   ├── client/               # Clientes HTTP para microservicios externos
│   ├── controllers/          # Lógica de negocio
│   ├── core/                 # Configuración, database, seguridad
│   │   ├── config.py         # Variables de entorno (Pydantic Settings)
│   │   └── database.py       # Engine SQLAlchemy y sesiones
│   ├── dao/                  # Data Access Objects (CRUD)
│   ├── models/               # Modelos SQLAlchemy (tablas)
│   ├── schemas/              # Schemas Pydantic (validación)
│   ├── services/             # Routers FastAPI
│   ├── templates/            # Templates HTML (reportes)
│   └── utils/                # Utilidades y excepciones
│
├── scripts/                  # Scripts de utilidad
├── tests/                    # Tests unitarios y de integración
│   ├── controllers/          # Tests de controladores
│   ├── routers/              # Tests de endpoints
│   └── conftest.py           # Fixtures compartidas
│
├── main.py                   # Punto de entrada de la aplicación
├── pyproject.toml            # Configuración del proyecto y dependencias
├── docker-compose.yml        # Microservicio externo de usuarios
└── .env                      # Variables de entorno (NO versionado)
```

---

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Python 3.11+** instalado
- **PostgreSQL** instalado y funcionando
- **uv** (gestor de paquetes recomendado)
- **Docker** (opcional, para microservicio externo)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/BackendFutbol.git
cd BackendFutbol
```

### 2. Instalar uv (si no lo tienes)

```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Instalar dependencias

```bash
# Instala todas las dependencias del proyecto
uv sync

# Para desarrollo (incluye Ruff)
uv sync --all-extras --dev
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# ================= BASE DE DATOS =================
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_password_seguro
DB_NAME=kallpa_unl_db

# ================= APLICACIÓN =================
APP_NAME=Kallpa UNL API
APP_VERSION=1.0.0
APP_PORT=8000
APP_HOST=0.0.0.0
DEBUG=True

# ================= SEGURIDAD (JWT) =================
JWT_SECRET=tu_secreto_super_seguro_aqui_minimo_32_caracteres
JWT_ALGORITHM=HS256
TOKEN_EXPIRES=3600
REFRESH_TOKEN_EXPIRES=604800

# ================= CORS =================
ALLOWED_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# ================= MICROSERVICIO EXTERNO =================
PERSON_MS_BASE_URL=http://localhost:8096
PERSON_MS_ADMIN_EMAIL=admin@admin.com
PERSON_MS_ADMIN_PASSWORD=12345678

# ================= EMAIL (SMTP) =================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_app_password
SMTP_FROM=tu_correo@gmail.com
SMTP_SSL=True
FRONTEND_URL=http://localhost:5173
```

### 5. Configurar PostgreSQL

#### Instalar PostgreSQL

**Windows:**

1. Descargar desde [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
2. Ejecutar el instalador y seguir los pasos
3. Recordar la contraseña del usuario `postgres` que configures

**macOS:**

```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Crear usuario y base de datos

Conectarse a PostgreSQL como superusuario:

```bash
# Windows (desde cmd o PowerShell)
psql -U postgres

# macOS/Linux
sudo -u postgres psql
```

Ejecutar los siguientes comandos SQL:

```sql
-- 1. Crear usuario para la aplicación
CREATE USER dev_user WITH PASSWORD 'dev_password';

-- 2. Crear la base de datos
CREATE DATABASE futbol_db OWNER dev_user;

-- 3. Otorgar todos los privilegios
GRANT ALL PRIVILEGES ON DATABASE futbol_db TO dev_user;

-- 4. Conectarse a la base de datos y otorgar permisos en el schema
\c futbol_db
GRANT ALL ON SCHEMA public TO dev_user;

-- 5. Salir
\q
```

#### Verificar conexión

```bash
# Probar conexión con el nuevo usuario
psql -U dev_user -d futbol_db -h localhost
```

#### Configurar .env

Asegúrate de que tu archivo `.env` coincida con los datos creados:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=dev_user
DB_PASSWORD=dev_password
DB_NAME=futbol_db
```

> **Nota**: Las tablas se crean automáticamente al iniciar la aplicación gracias a `Base.metadata.create_all()` en `main.py`.

### 6. Iniciar el microservicio externo (opcional)

Levantar el microservicio de usuarios externo:

```bash
docker-compose up -d
```

Esto levanta:

- MariaDB en puerto `3306`
- Microservicio Spring Boot en puerto `8096`

---

## ▶️ Ejecutar la Aplicación

### Desarrollo (con recarga automática)

```bash
# Opción recomendada
uv run python main.py

# Alternativa con uvicorn
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Producción

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📚 Documentación API

Una vez iniciado el servidor:

| Documentación                 | URL                                |
| ----------------------------- | ---------------------------------- |
| **Scalar Docs** (Recomendado) | http://localhost:8000/scalar       |
| **Swagger UI**                | http://localhost:8000/docs         |
| **ReDoc**                     | http://localhost:8000/redoc        |
| **OpenAPI JSON**              | http://localhost:8000/openapi.json |

---

## 🧪 Ejecutar Tests

```bash
# Ejecutar todos los tests
uv run pytest

# Con cobertura
uv run pytest --cov=app --cov-report=term-missing

# Tests específicos
uv run pytest tests/controllers/test_user_controller.py -v

# Solo tests que coincidan con un patrón
uv run pytest -k "create_user"
```

---

## 🔍 Linting y Formato

```bash
# Verificar formato
uv run ruff format --check .

# Aplicar formato
uv run ruff format .

# Verificar errores de código
uv run ruff check .

# Corregir errores automáticamente
uv run ruff check --fix .
```

---

## 🔄 Pipelines CI/CD

El proyecto tiene 3 pipelines de GitHub Actions:

### 1. `fastapi-ci.yml` (PRs a `development`)

- ✅ Verifica formato (Ruff)
- ✅ Ejecuta linter (Ruff)
- ✅ Ejecuta tests (pytest)

### 2. `staging-ci.yml` (PRs a `staging`)

- ✅ Todo lo anterior
- ✅ Cobertura mínima requerida

### 3. `production-ci.yml` (PRs a `main`)

- ✅ Todo lo anterior
- ✅ Análisis de seguridad (Bandit)
- ✅ Análisis de vulnerabilidades (Safety)
- ✅ Cobertura mínima: 60%

---

## 🌳 Flujo de Trabajo Git

### Estructura de Ramas

| Rama          | Entorno    | Descripción                              |
| ------------- | ---------- | ---------------------------------------- |
| `main`        | Producción | Código estable. **No commits directos.** |
| `staging`     | QA/Pruebas | Entorno de testing pre-producción        |
| `development` | Desarrollo | Rama de integración principal            |

### Crear una nueva feature

```bash
# 1. Actualizar development
git checkout development
git pull origin development

# 2. Crear rama feature
git checkout -b feature/HS-XXX-descripcion

# 3. Desarrollar y hacer commits
git add .
git commit -m "feat: descripción del cambio"

# 4. Push y crear PR
git push origin feature/HS-XXX-descripcion
```

### Convención de commits

```
feat: nueva funcionalidad
fix: corrección de bug
docs: documentación
test: tests
refactor: refactorización
style: formato/estilo
```

---

## 📦 Despliegue en Producción

### Opción 1: Servidor tradicional (VPS/EC2)

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/BackendFutbol.git
cd BackendFutbol

# 2. Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Instalar dependencias
uv sync

# 4. Configurar .env con valores de producción
cp .env.example .env
nano .env  # Editar con valores reales

# 5. Ejecutar con Gunicorn (recomendado para producción)
uv pip install gunicorn
uv run gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Opción 2: Docker

```dockerfile
# Dockerfile (crear en raíz del proyecto)
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t kallpa-backend .
docker run -d -p 8000:8000 --env-file .env kallpa-backend
```

### Variables de entorno críticas para producción

```env
DEBUG=False
JWT_SECRET=<secreto_muy_largo_y_seguro>
DB_PASSWORD=<password_seguro>
ALLOWED_ORIGINS=["https://tu-dominio.com"]
```

---

## 🔐 Seguridad

- **Autenticación**: JWT con tokens de acceso y refresh
- **Contraseñas**: Hasheadas con bcrypt
- **CORS**: Configurado para dominios específicos
- **Validación**: Pydantic valida todas las entradas
- **DNI**: Validación completa de cédula ecuatoriana

---

## 📊 Módulos Principales

| Módulo           | Descripción                               |
| ---------------- | ----------------------------------------- |
| **Usuarios**     | Gestión de administradores y entrenadores |
| **Atletas**      | Registro y seguimiento de deportistas     |
| **Evaluaciones** | Tests físicos y mediciones                |
| **Asistencia**   | Control de asistencia a entrenamientos    |
| **Estadísticas** | Métricas y reportes de rendimiento        |
| **Reportes**     | Generación de PDF/Excel                   |

---

## 🐛 Solución de Problemas

### Error de conexión a PostgreSQL

```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar credenciales en .env
```

### Error de microservicio externo

```bash
# Verificar que docker-compose esté corriendo
docker-compose ps

# Reiniciar servicios
docker-compose down && docker-compose up -d
```

### Tests fallan por configuración

```bash
# Verificar que las variables de entorno estén configuradas
cat .env
```

---

## 📄 Licencia

Este proyecto es parte de la Universidad Nacional de Loja.

---

**Desarrollado con ❤️ para la gestión deportiva universitaria**
