"""Esquema de respuesta estándar para endpoints FastAPI."""

from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T] = None
    errors: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}
