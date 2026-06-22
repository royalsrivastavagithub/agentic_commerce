from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.cart import CartProductInfo


class WishlistItemCreate(BaseModel):
    product_id: int


class WishlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product: CartProductInfo
    created_at: datetime
