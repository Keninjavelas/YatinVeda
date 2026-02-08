"""
Pydantic validation schemas for request/response models
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    """Enhanced user creation schema with strong password validation"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v:
            raise ValueError('Username cannot be empty')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password exceeds bcrypt 72-byte limit; reduce multi-byte characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
