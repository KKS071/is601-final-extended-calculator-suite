# File: app/schemas/user.py
# Purpose: Pydantic schemas for user registration, login, update, and response.
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name:  str = Field(min_length=1, max_length=50)
    email:      EmailStr
    username:   str = Field(min_length=3, max_length=50)

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password:         str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def verify_password_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @model_validator(mode="after")
    def validate_password_strength(self) -> "UserCreate":
        p = self.password
        if not any(c.isupper() for c in p):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in p):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in p):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in p):
            raise ValueError("Password must contain at least one special character")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "username": "johndoe",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
            }
        }
    )


class UserResponse(BaseModel):
    id:         UUID
    username:   str
    email:      EmailStr
    first_name: str
    last_name:  str
    is_active:  bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={"example": {"username": "johndoe", "password": "SecurePass123!"}}
    )


class UserUpdate(BaseModel):
    first_name: Optional[str]      = Field(None, min_length=1, max_length=50)
    last_name:  Optional[str]      = Field(None, min_length=1, max_length=50)
    email:      Optional[EmailStr] = None
    username:   Optional[str]      = Field(None, min_length=3, max_length=50)

    model_config = ConfigDict(from_attributes=True)


class PasswordUpdate(BaseModel):
    current_password:     str = Field(min_length=8, max_length=128)
    new_password:         str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def verify_passwords(self) -> "PasswordUpdate":
        if self.new_password != self.confirm_new_password:
            raise ValueError("New password and confirmation do not match")
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current password")
        return self
