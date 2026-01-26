"""Punto de entrada de la aplicación FastAPI."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import http_exception_handler
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
from app.utils.exceptions import AppException, DatabaseException, EmailServiceException

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

    # CORS para permitir front-end en dev/prod
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # app.add_middleware(ErrorHandlerMiddleware)
    # app.add_middleware(LoggingMiddleware)

    # Scalar docs
    setup_scalar_docs(app)

    # CORS (necesario para frontend en http://localhost:5173)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Manejo de validación
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        error_map: dict[str, list[str]] = {}
        for error in exc.errors():
            # loc típico: ('body', 'field') o ('query', 'page')
            loc = error.get("loc") or ()
            field = ".".join(str(x) for x in loc) if loc else "__root__"
            msg = error.get("msg") or "Valor inválido"
            error_map.setdefault(field, []).append(str(msg))

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": "Error de validación. Revisa los campos enviados.",
                "data": None,
                "errors": error_map,
            },
        )

    # Manejo de excepciones de aplicación (AppException y subclases)
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.message,
                "data": None,
                "errors": None,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler_wrapped(
        request: Request, exc: StarletteHTTPException
    ):
        # Preserva comportamiento estándar para endpoints que no usan ResponseSchema,
        # pero envuelve el payload cuando sea posible para que el frontend tenga mssg.
        if isinstance(exc.detail, (dict, list)):
            # Si ya es un objeto estructurado, dejamos que FastAPI lo renderice.
            return await http_exception_handler(request, exc)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": str(exc.detail) if exc.detail else "Error",
                "data": None,
                "errors": None,
            },
        )

    # Manejador para errores de base de datos (conexión, timeouts, etc.)
    @app.exception_handler(OperationalError)
    async def database_operational_error_handler(
        request: Request, exc: OperationalError
    ):
        logger.error(f"Database operational error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": (
                    "Estamos teniendo problemas con el servicio. "
                    "Por favor, intente nuevamente más tarde."
                ),
                "data": None,
                "errors": None,
            },
        )

    @app.exception_handler(InterfaceError)
    async def database_interface_error_handler(request: Request, exc: InterfaceError):
        logger.error(f"Database interface error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": (
                    "Estamos teniendo problemas con el servicio. "
                    "Por favor, intente nuevamente más tarde."
                ),
                "data": None,
                "errors": None,
            },
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        logger.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": (
                    "Estamos teniendo problemas con el servicio. "
                    "Por favor, intente nuevamente más tarde."
                ),
                "data": None,
                "errors": None,
            },
        )

    @app.exception_handler(DatabaseException)
    async def custom_database_exception_handler(
        request: Request, exc: DatabaseException
    ):
        logger.error(f"Custom database exception: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": (
                    "Estamos teniendo problemas con el servicio. "
                    "Por favor, intente nuevamente más tarde."
                ),
                "data": None,
                "errors": None,
            },
        )

    # Manejador para errores del servicio de correo (SMTP)
    @app.exception_handler(EmailServiceException)
    async def email_service_exception_handler(
        request: Request, exc: EmailServiceException
    ):
        logger.error(f"Email service exception: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": exc.message,
                "data": None,
                "errors": None,
            },
        )

    # Manejador global para excepciones no capturadas (catch-all)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": (
                    "Ha ocurrido un error inesperado."
                    "Por favor, intente nuevamente más tarde."
                ),
                "data": None,
                "errors": None,
            },
        )

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

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/scalar")

    @app.get("/health", tags=["Health"], response_model=ResponseSchema)
    async def health_check():
        """
        Verifica el estado de salud de la API y sus dependencias.

        Realiza verificaciones de:
        - Conexión a la base de datos
        - Estado general de la aplicación
        """
        from sqlalchemy import text

        from app.core.database import SessionLocal

        health_status = {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": "development" if settings.DEBUG else "production",
            "database": "unknown",
        }

        # Verificar conexión a la base de datos
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
                    "message": (
                        "Estamos teniendo problemas con el servicio. "
                        "Por favor, intente nuevamente más tarde."
                    ),
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
        """
        Verificación de vida simple (para kubernetes/docker).
        Solo verifica que la aplicación está corriendo.
        """
        return {"status": "alive"}

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """
        Verificación de preparación (para kubernetes/docker).
        Verifica que la aplicación está lista para recibir tráfico.
        """
        from sqlalchemy import text

        from app.core.database import SessionLocal

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

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
