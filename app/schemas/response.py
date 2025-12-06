"""Esquema de respuesta estándar para endpoints FastAPI."""

from pydantic import BaseModel
from typing import Any, Optional, Dict


class ResponseSchema(BaseModel):
    """Envuelve estado, mensaje, datos y errores opcionales."""

    status: str  # "success" | "error"
    message: str
    data: Optional[Any] = None
    errors: Optional[Dict[str, Any]] = None
    
    model_config = {"json_schema_extra": {
        "example": {
            "status": "success",
            "message": "Operación realizada correctamente",
            "data": {"id": 1}
        }
    }}
