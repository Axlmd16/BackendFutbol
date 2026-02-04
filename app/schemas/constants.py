"""Constantes compartidas para esquemas de validación."""

import re

# FORMATOS DE FECHA Y HORA

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# Mensajes de formato
DATE_FORMAT_DESCRIPTION = "YYYY-MM-DD"
TIME_FORMAT_DESCRIPTION = "HH:MM"

# MENSAJES DE ERROR COMUNES

DATE_FORMAT_ERROR = (
    "Formato de fecha inválido. Use el formato YYYY-MM-DD (ejemplo: 2024-01-15)"
)
TIME_FORMAT_ERROR = (
    "Formato de hora inválido. Use el formato HH:MM (ejemplo: 08:30, 14:00)"
)
TIME_RANGE_ERROR = (
    "Formato de hora inválido. Use el formato HH:MM "
    "(ejemplo: 08:30, 14:00). La hora debe estar entre 00:00 y 23:59"
)
FUTURE_DATE_ERROR = "No se puede registrar asistencia para fechas futuras."

# PATRONES REGEX COMPILADOS

# Patrón para teléfono ecuatoriano (10 dígitos, empieza con 0)
PHONE_PATTERN_EC = re.compile(r"^0\d{9}$")
PHONE_PATTERN_EC_STR = r"^0\d{9}$"

# Patrón para hora HH:MM
TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")
TIME_PATTERN_STRICT = re.compile(r"^\d{2}:\d{2}$")

# Patrón para nombres (solo letras y espacios, incluyendo acentos)
NAME_PATTERN = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")

# MENSAJES DE VALIDACIÓN DE TELÉFONO

PHONE_FORMAT_ERROR_EC = "El teléfono debe tener 10 dígitos y comenzar con 0"
PHONE_FORMAT_ERROR_FULL = (
    "Formato de teléfono inválido. Use formato ecuatoriano: "
    "09XXXXXXXX, 07XXXXXXX o +593XXXXXXXXX"
)

# MENSAJES DE ERROR DE SERVICIO
SERVICE_PROBLEMS_MSG = (
    "Estamos teniendo problemas con el servicio. "
    "Por favor, intente nuevamente más tarde."
)

# VALORES POR DEFECTO
DEFAULT_DIRECTION = "S/N"
DEFAULT_PHONE = "S/N"
DEFAULT_TYPE_IDENTIFICATION = "CEDULA"

# LÍMITES DE LONGITUD
MAX_DIRECTION_LENGTH = 500
MAX_EMAIL_LENGTH = 254
MAX_NAME_LENGTH = 100
MIN_NAME_LENGTH = 2
