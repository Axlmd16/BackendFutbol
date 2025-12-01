from pydantic import EmailStr, Field, field_validator
from typing import Optional
from app.schemas.base_schema import BaseSchema, BaseResponseSchema

class UserBase(BaseSchema):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    
    # @field_validator('password')
    # def validate_password(cls, v):
    #     if not any(char.isdigit() for char in v):
    #         raise ValueError('La contraseña debe contener al menos un número')
    #     if not any(char.isupper() for char in v):
    #         raise ValueError('La contraseña debe contener al menos una mayúscula')
    #     return v

class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(BaseResponseSchema, UserBase):
    pass

class UserLogin(BaseSchema):
    email: EmailStr
    password: str