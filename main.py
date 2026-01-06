"""Punto de entrada de la aplicación FastAPI."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
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
from app.utils.exceptions import AppException

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

    logger.info("🚀 Starting application...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as exc:  # pragma: no cover - se registra el fallo
        logger.error(f"Error creating tables: {exc}")

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
        return ResponseSchema(
            status="success",
            message="API funcionando correctamente",
            data={
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": "development" if settings.DEBUG else "production",
            },
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
