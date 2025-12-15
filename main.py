from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import sys

from app.core.config import settings
from app.core.database import engine, Base
from app.core.docs import get_openapi_config, get_tags_metadata
from app.models import *  # noqa: F401, F403
# from app.core.middleware import setup_cors, ErrorHandlerMiddleware, LoggingMiddleware
from app.core.scalar_docs import setup_scalar_docs

from app.schemas.response import ResponseSchema
from app.services.routers import athlete_router
from app.services.routers import inscription_router
from app.services.routers import test_router
from app.services.routers import evaluation_router
from app.services.routers import attendance_router
from app.services.routers import statistic_router
from app.services.routers import sprint_test_router
from app.services.routers import endurance_test_router
from app.services.routers import yoyo_test_router
from app.services.routers import technical_assessment_router
from app.services.routers import user_router
from app.services.routers import account_router

# Configuración de logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de ciclo de vida"""
    logger.info("🚀 Starting application...")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
    
    logger.info(f"📊 Scalar Docs: http://{settings.APP_HOST}:{settings.APP_PORT}/scalar")
    logger.info("✅ Application started")
    
    yield
    
    logger.info("🛑 Shutting down...")


def create_application() -> FastAPI:
    """Factory para crear la aplicación"""
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
        lifespan=lifespan
    )
    
    # Middlewares
    # setup_cors(app)
    # app.add_middleware(ErrorHandlerMiddleware)
    # app.add_middleware(LoggingMiddleware)
    
    # Scalar docs
    setup_scalar_docs(app)
    
    # Manejo de validación
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = [{
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        } for error in exc.errors()]
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": "Error de validación",
                "data": None,
                "errors": errors
            }
        )
    
    # Routers
    API_PREFIX = "/api/v1"
    app.include_router(athlete_router, prefix=API_PREFIX)
    app.include_router(inscription_router, prefix=API_PREFIX)
    app.include_router(test_router, prefix=API_PREFIX)
    app.include_router(evaluation_router, prefix=API_PREFIX)
    app.include_router(attendance_router, prefix=API_PREFIX)
    app.include_router(statistic_router, prefix=API_PREFIX)
    app.include_router(sprint_test_router, prefix=API_PREFIX)
    app.include_router(endurance_test_router, prefix=API_PREFIX)
    app.include_router(yoyo_test_router, prefix=API_PREFIX)
    app.include_router(technical_assessment_router, prefix=API_PREFIX)
    app.include_router(user_router, prefix=API_PREFIX)
    app.include_router(account_router, prefix=API_PREFIX)
    
    # Endpoints base
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
                "environment": "development" if settings.DEBUG else "production"
            }
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
                    "scalar": f"http://{settings.APP_HOST}:{settings.APP_PORT}/scalar"
                }
            }
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
        log_level="debug" if settings.DEBUG else "info"
    )