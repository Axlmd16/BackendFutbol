"""Excepciones personalizadas para controlar errores de la API."""


class AppException(Exception):
    """Excepción base con mensaje y status code HTTP."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Se lanza cuando un recurso no existe."""

    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, status_code=404)


class AlreadyExistsException(AppException):
    """Se lanza cuando se intenta crear un duplicado."""

    def __init__(self, message: str = "El recurso ya existe"):
        super().__init__(message, status_code=409)


class ValidationException(AppException):
    """Datos inválidos o reglas de negocio incumplidas."""

    def __init__(self, message: str = "Error de validación", detail: str = None):
        super().__init__(message, status_code=422)
        self.detail = detail

    def to_dict(self):
        return {"message": self.message, "detail": self.detail}


class UnauthorizedException(AppException):
    """Operación sin credenciales o permisos."""

    def __init__(self, message: str = "No autorizado"):
        super().__init__(message, status_code=401)


class DatabaseException(AppException):
    """Errores de persistencia o integridad en la BD."""

    def __init__(self, message: str = "Error de base de datos"):
        super().__init__(message, status_code=500)


class EmailServiceException(AppException):
    """Errores del servicio de correo electrónico (SMTP)."""

    def __init__(
        self,
        message: str = (
            "No se pudo enviar el correo electrónico. "
            "Por favor, intente nuevamente más tarde."
        ),
    ):
        super().__init__(message, status_code=503)


class ExternalServiceException(AppException):
    """Errores de servicios externos (APIs, microservicios, etc.)."""

    def __init__(
        self,
        message: str = (
            "El servicio externo no está disponible. "
            "Por favor, intente nuevamente más tarde."
        ),
    ):
        super().__init__(message, status_code=503)
