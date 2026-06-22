from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Optional[str] = None
    email: str


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str
    user: UserInfo
    created_at: datetime
    updated_at: datetime
