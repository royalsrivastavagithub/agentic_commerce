from typing import Optional

from pydantic import BaseModel, ConfigDict


class AddressBase(BaseModel):
    label: str = "Home"
    street: str
    city: str
    state: str
    pincode: str
    country: str = "India"
    is_default: bool = False
    address_type: str = "both"  # shipping, billing, both


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None
    address_type: Optional[str] = None


class AddressResponse(AddressBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
