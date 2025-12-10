"""Pydantic schemas for user operations."""

from pydantic import BaseModel, EmailStr, Field

class AdminCreateUserRequest(BaseModel):
    """Payload required for admin-created users."""

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    institutional_email: EmailStr = Field(..., description="Corporate email of the user")
    dni: str = Field(..., min_length=10, max_length=10, description="Ecuadorian DNI (10 digits)")
    role: str = Field(..., description="administrator or coach")

class AdminCreateUserResponse(BaseModel):
    """Minimal user/account data after creation."""

    user_id: int
    account_id: int
    email: EmailStr
    role: str
