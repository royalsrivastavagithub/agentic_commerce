from datetime import date
from typing import Optional
import re

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

from app.schemas.address import AddressResponse

PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9\s])[\S]{8,16}$'


class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=16)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                "Password must be 8-16 characters with at least one uppercase, "
                "one lowercase, one digit, and one symbol"
            )
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    role: str = "user"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    addresses: list[AddressResponse] = []

    model_config = ConfigDict(from_attributes=True)

class UserVerify(BaseModel):
    token: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
