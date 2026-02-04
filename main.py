"""Punto de entrada de la aplicación FastAPI."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import DatabaseError, InterfaceError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import Base, engine
from app.core.docs import get_openapi_config, get_tags_metadata
from app.core.scalar_docs import setup_scalar_docs
from app.models import *  # noqa: F401, F403
from app.schemas.constants import SERVICE_PROBLEMS_MSG
from app.schemas.response import ResponseSchema
from app.services.routers import (
    account_router,
    athlete_router,
    attendance_router,
    endurance_test_router,
    evaluation_router,
    report_router,
    representative_router,
    sprint_test_router,
    statistic_router,
    technical_assessment_router,
    test_router,
    user_router,
    yoyo_test_router,
)
from app.utils.exceptions import (
    AppException,
    DatabaseException,
    EmailServiceException,
    ExternalServiceException,
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
# Suprimir logs ruidosos de librerías externas
logging.getLogger("fontTools").setLevel(logging.WARNING)
logging.getLogger("weasyprint").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("multipart").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de ciclo de vida."""
    from app.core.database import SessionLocal
    from app.core.seeder import seed_default_admin

    logger.info("🚀 Starting application...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")

        # Crear usuario admin por defecto
        db = SessionLocal()
        try:
            seed_default_admin(db)
        finally:
            db.close()

    except Exception as exc:  # pragma: no cover - se registra el fallo
        logger.error(f"Error creating tables or seeding: {exc}")

    logger.info(
        f"📊 Scalar Docs: http://{settings.APP_HOST}:{settings.APP_PORT}/scalar"
    )
    logger.info("✅ Application started")

    yield

    logger.info("🛑 Shutting down...")


def _configure_middlewares(app: FastAPI) -> None:
    """Configura los middlewares de la aplicación."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los manejadores de excepciones."""
    from app.core.exception_handlers import (
        app_exception_handler,
        custom_database_exception_handler,
        database_error_handler,
        database_interface_error_handler,
        database_operational_error_handler,
        email_service_exception_handler,
        external_service_exception_handler,
        global_exception_handler,
        http_exception_handler_wrapped,
        validation_exception_handler,
    )

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler_wrapped)
    app.add_exception_handler(OperationalError, database_operational_error_handler)
    app.add_exception_handler(InterfaceError, database_interface_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(DatabaseException, custom_database_exception_handler)
    app.add_exception_handler(EmailServiceException, email_service_exception_handler)
    app.add_exception_handler(
        ExternalServiceException, external_service_exception_handler
    )
    app.add_exception_handler(Exception, global_exception_handler)


def _register_routers(app: FastAPI) -> None:
    """Registra todos los routers de la API."""
    API_PREFIX = "/api/v1"
    app.include_router(athlete_router, prefix=API_PREFIX)
    app.include_router(user_router, prefix=API_PREFIX)
    app.include_router(account_router, prefix=API_PREFIX)
    app.include_router(test_router, prefix=API_PREFIX)
    app.include_router(evaluation_router, prefix=API_PREFIX)
    app.include_router(attendance_router, prefix=API_PREFIX)
    app.include_router(statistic_router, prefix=API_PREFIX)
    app.include_router(sprint_test_router, prefix=API_PREFIX)
    app.include_router(endurance_test_router, prefix=API_PREFIX)
    app.include_router(yoyo_test_router, prefix=API_PREFIX)
    app.include_router(technical_assessment_router, prefix=API_PREFIX)
    app.include_router(representative_router, prefix=API_PREFIX)
    app.include_router(report_router, prefix=API_PREFIX)


def _register_health_endpoints(app: FastAPI) -> None:
    """Registra los endpoints de salud y utilidad."""
    from sqlalchemy import text

    from app.core.database import SessionLocal

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/scalar")

    @app.get("/health", tags=["Health"], response_model=ResponseSchema)
    async def health_check():
        """Verifica el estado de salud de la API y sus dependencias."""
        health_status = {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": "development" if settings.DEBUG else "production",
            "database": "unknown",
        }

        try:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                health_status["database"] = "connected"
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Health check - Database connection failed: {e}")
            health_status["database"] = "disconnected"
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "error",
                    "message": SERVICE_PROBLEMS_MSG,
                    "data": health_status,
                    "errors": None,
                },
            )

        return ResponseSchema(
            status="success",
            message="API funcionando correctamente",
            data=health_status,
        )

    @app.get("/health/live", tags=["Health"])
    async def liveness_check():
        """Verificación de vida simple (para kubernetes/docker)."""
        return {"status": "alive"}

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """Verificación de preparación (para kubernetes/docker)."""
        try:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
            finally:
                db.close()
            return {"status": "ready"}
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "reason": "database_unavailable"},
            )

    @app.get("/info", tags=["Health"], response_model=ResponseSchema)
    async def api_info():
        return ResponseSchema(
            status="success",
            message="Información de la API",
            data={
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "docs": {
                    "swagger": f"http://{settings.APP_HOST}:{settings.APP_PORT}/docs",
                    "redoc": f"http://{settings.APP_HOST}:{settings.APP_PORT}/redoc",
                    "scalar": f"http://{settings.APP_HOST}:{settings.APP_PORT}/scalar",
                },
            },
        )


def create_application() -> FastAPI:
    """Factory para crear la aplicación."""
    openapi_config = get_openapi_config()

    app = FastAPI(
        title=openapi_config["title"],
        version=openapi_config["version"],
        description=openapi_config["description"],
        contact=openapi_config["contact"],
        license_info=openapi_config["license_info"],
        openapi_tags=get_tags_metadata(),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    _configure_middlewares(app)
    setup_scalar_docs(app)
    _register_exception_handlers(app)
    _register_routers(app)
    _register_health_endpoints(app)

    return app


app = create_application()


if __name__ == "__main__":
    import os

    import uvicorn

    # Fórmula (2 * CPU cores) + 1
    workers = 1 if settings.DEBUG else int(os.getenv("UVICORN_WORKERS", 4))

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        workers=workers if not settings.DEBUG else 1,  # reload no soporta workers
        log_level="debug" if settings.DEBUG else "info",
        limit_concurrency=200,  # Aumentado para soportar más carga
        limit_max_requests=50000,  # Más requests antes de reiniciar
        timeout_keep_alive=60,  # Mayor tiempo de keep-alive
        backlog=2048,  # Cola de conexiones pendientes
    )
