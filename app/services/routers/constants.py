"""Constantes compartidas para routers."""

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
