"""Constantes compartidas para routers."""

from typing import TypeVar

from fastapi.responses import JSONResponse

from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException

T = TypeVar("T")

# ===========================================
# MENSAJES DE ERROR COMUNES
# ===========================================
UNEXPECTED_ERROR_PREFIX = "Error inesperado"


def unexpected_error_message(error: Exception) -> str:
    """Genera un mensaje de error inesperado estandarizado.

    Args:
        error: La excepción que ocurrió.

    Returns:
        Mensaje de error formateado.
    """
    return f"{UNEXPECTED_ERROR_PREFIX}: {str(error)}"


def handle_app_exception(exc: AppException) -> JSONResponse:
    """Crea respuesta JSON para AppException.

    Args:
        exc: La excepción de aplicación.

    Returns:
        JSONResponse con el error formateado.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseSchema(
            status="error",
            message=exc.message,
            data=None,
            errors=None,
        ).model_dump(),
    )


def handle_unexpected_exception(exc: Exception, status_code: int = 500) -> JSONResponse:
    """Crea respuesta JSON para excepciones inesperadas.

    Args:
        exc: La excepción que ocurrió.
        status_code: Código HTTP de respuesta.

    Returns:
        JSONResponse con el error formateado.
    """
    return JSONResponse(
        status_code=status_code,
        content=ResponseSchema(
            status="error",
            message=unexpected_error_message(exc),
            data=None,
            errors=None,
        ).model_dump(),
    )


# ===========================================
# MENSAJES DE RESPUESTA EXITOSA
# ===========================================
SUCCESS_CREATED = "creado correctamente"
SUCCESS_UPDATED = "actualizado correctamente"
SUCCESS_DELETED = "eliminado correctamente"

# ===========================================
# STATUS STRINGS
# ===========================================
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
