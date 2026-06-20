from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DimensionSchema(BaseModel):
    width: float
    height: float
    depth: float


class ReviewSchema(BaseModel):
    rating: int
    comment: str
    date: str
    reviewerName: str
    reviewerEmail: str


class MetaSchema(BaseModel):
    createdAt: str
    updatedAt: str
    barcode: str
    qrCode: str


class ProductSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    title: str
    description: str
    category_id: int
    category: str
    price: float
    discount_percentage: float = Field(alias="discountPercentage")
    rating: float
    stock: int
    tags: list[str]
    brand: Optional[str] = None
    sku: str
    weight: float
    dimensions: DimensionSchema
    warranty_information: str = Field(alias="warrantyInformation")
    shipping_information: str = Field(alias="shippingInformation")
    availability_status: str = Field(alias="availabilityStatus")
    reviews: list[ReviewSchema]
    return_policy: str = Field(alias="returnPolicy")
    minimum_order_quantity: int = Field(alias="minimumOrderQuantity")
    meta: MetaSchema
    images: list[str]
    thumbnail: str


class ProductCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
    title: str
    description: str
    category_id: int
    price: float
    discount_percentage: float = Field(alias="discountPercentage")
    rating: float
    stock: int
    tags: list[str]
    brand: Optional[str] = None
    sku: str
    weight: float
    dimensions: DimensionSchema
    warranty_information: str = Field(alias="warrantyInformation")
    shipping_information: str = Field(alias="shippingInformation")
    availability_status: str = Field(alias="availabilityStatus")
    reviews: list[ReviewSchema]
    return_policy: str = Field(alias="returnPolicy")
    minimum_order_quantity: int = Field(alias="minimumOrderQuantity")
    meta: MetaSchema
    images: list[str]
    thumbnail: str


class ProductUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = None
    discount_percentage: Optional[float] = Field(default=None, alias="discountPercentage")
    rating: Optional[float] = None
    stock: Optional[int] = None
    tags: Optional[list[str]] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[DimensionSchema] = None
    warranty_information: Optional[str] = Field(default=None, alias="warrantyInformation")
    shipping_information: Optional[str] = Field(default=None, alias="shippingInformation")
    availability_status: Optional[str] = Field(default=None, alias="availabilityStatus")
    reviews: Optional[list[ReviewSchema]] = None
    return_policy: Optional[str] = Field(default=None, alias="returnPolicy")
    minimum_order_quantity: Optional[int] = Field(default=None, alias="minimumOrderQuantity")
    meta: Optional[MetaSchema] = None
    images: Optional[list[str]] = None
    thumbnail: Optional[str] = None


class ProductsResponse(BaseModel):
    products: list[ProductSchema]
    total: int
    skip: int
    limit: int
