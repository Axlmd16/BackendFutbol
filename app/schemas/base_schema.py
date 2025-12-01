from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    """Schema base con configuración común"""
    model_config = ConfigDict(from_attributes=True)

class BaseResponseSchema(BaseSchema):
    """Schema para respuestas que incluyen timestamps"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
