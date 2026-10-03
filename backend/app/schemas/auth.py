from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="User full name")
    email: str = Field(..., description="Valid unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="User password (min 6 characters)")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: Optional[str] = None


class RegisterResponse(BaseModel):
    message: str = "Registration successful"
    user: UserResponse


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: UserResponse
