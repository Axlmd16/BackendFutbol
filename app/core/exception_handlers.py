"""Manejadores de excepciones para la aplicación FastAPI."""

import logging

from fastapi import Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DatabaseError, InterfaceError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.constants import SERVICE_PROBLEMS_MSG
from app.utils.exceptions import (
    AppException,
    DatabaseException,
    EmailServiceException,
    ExternalServiceException,
)

logger = logging.getLogger(__name__)

# Diccionario de traducciones de mensajes comunes de Pydantic
PYDANTIC_TRANSLATIONS = {
    "Field required": "Este campo es obligatorio",
    "field required": "Este campo es obligatorio",
    "value is not a valid integer": "El valor debe ser un número entero",
    "value is not a valid float": "El valor debe ser un número decimal",
    "value is not a valid email address": "El correo electrónico no es válido",
    "ensure this value has at least": "Este campo debe tener al menos",
    "ensure this value has at most": "Este campo debe tener como máximo",
    "string does not match regex": "El formato no es válido",
    "value is not a valid list": "El valor debe ser una lista",
    "value is not a valid dict": "El valor debe ser un objeto",
    "Input should be a valid integer": "El valor debe ser un número entero",
    "Input should be a valid string": "El valor debe ser texto",
    "Input should be a valid boolean": "El valor debe ser verdadero o falso",
    "Input should be a valid list": "El valor debe ser una lista",
    "Input should be greater than or equal to 1": "El valor debe ser mayor o igual a 1",
    "String should have at least": "El texto debe tener al menos",
    "List should have at least 1 item after validation, not 0": (
        "La lista de registros no puede estar vacía. Debe incluir al menos un registro."
    ),
}


def _translate_message(msg: str) -> str:
    """Traduce mensajes comunes de Pydantic al español."""
    msg = msg.replace("Value error, ", "").replace("value_error, ", "")
    if msg in PYDANTIC_TRANSLATIONS:
        return PYDANTIC_TRANSLATIONS[msg]
    for eng, esp in PYDANTIC_TRANSLATIONS.items():
        if eng.lower() in msg.lower():
            return esp
    return msg


def _build_error_map(exc: RequestValidationError) -> tuple[dict, str | None]:
    """Construye el mapa de errores y extrae el mensaje principal."""
    error_map: dict[str, list[str]] = {}
    first_user_message = None

    for error in exc.errors():
        loc = error.get("loc") or ()
        msg = error.get("msg") or "Valor inválido"
        translated_msg = _translate_message(str(msg))

        if not loc or (len(loc) == 1 and loc[0] == "body"):
            if not first_user_message:
                first_user_message = translated_msg
            field = "__root__"
        else:
            field_parts = [str(x) for x in loc if x != "body"]
            field = ".".join(field_parts) if field_parts else "__root__"

        error_map.setdefault(field, []).append(translated_msg)

    return error_map, first_user_message


def _service_error_response(message: str = SERVICE_PROBLEMS_MSG) -> JSONResponse:
    """Genera una respuesta de error de servicio estándar."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "error",
            "message": message,
            "data": None,
            "errors": None,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Manejador para errores de validación de Pydantic."""
    error_map, first_user_message = _build_error_map(exc)
    main_message = (
        first_user_message or "Error de validación. Revisa los campos enviados."
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": main_message,
            "data": None,
            "errors": error_map,
        },
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Manejador para excepciones de aplicación (AppException y subclases)."""
    errors = {"__root__": [exc.message]} if exc.status_code == 422 else None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message,
            "data": None,
            "errors": errors,
        },
    )


async def http_exception_handler_wrapped(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Manejador para excepciones HTTP de Starlette."""
    if isinstance(exc.detail, (dict, list)):
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


async def database_operational_error_handler(
    request: Request, exc: OperationalError
) -> JSONResponse:
    """Manejador para errores operacionales de base de datos."""
    logger.error(f"Database operational error: {exc}")
    return _service_error_response()


async def database_interface_error_handler(
    request: Request, exc: InterfaceError
) -> JSONResponse:
    """Manejador para errores de interfaz de base de datos."""
    logger.error(f"Database interface error: {exc}")
    return _service_error_response()


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Manejador para errores generales de base de datos."""
    logger.error(f"Database error: {exc}")
    return _service_error_response()


async def custom_database_exception_handler(
    request: Request, exc: DatabaseException
) -> JSONResponse:
    """Manejador para excepciones de base de datos personalizadas."""
    logger.error(f"Custom database exception: {exc.message}")
    return _service_error_response()


async def email_service_exception_handler(
    request: Request, exc: EmailServiceException
) -> JSONResponse:
    """Manejador para errores del servicio de correo."""
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


async def external_service_exception_handler(
    request: Request, exc: ExternalServiceException
) -> JSONResponse:
    """Manejador para errores de servicios externos."""
    logger.error(f"External service exception: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "error",
            "message": exc.message,
            "data": None,
            "errors": None,
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Manejador global para excepciones no capturadas."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": (
                "Ha ocurrido un error inesperado. "
                "Por favor, intente nuevamente más tarde."
            ),
            "data": None,
            "errors": None,
        },
    )
