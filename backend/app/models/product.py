from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    discount_percentage = Column("discountPercentage", Float, nullable=False)
    rating = Column(Float, nullable=False, default=0)
    review_count = Column(Integer, nullable=False, default=0)
    stock = Column(Integer, nullable=False)
    tags = Column(JSON, nullable=False)
    brand = Column(String, nullable=True)
    sku = Column(String, nullable=False, unique=True)
    weight = Column(Float, nullable=False)
    dimensions = Column(JSON, nullable=False)
    warranty_information = Column("warrantyInformation", String, nullable=False)
    shipping_information = Column("shippingInformation", String, nullable=False)
    availability_status = Column("availabilityStatus", String, nullable=False)
    return_policy = Column("returnPolicy", String, nullable=False)
    minimum_order_quantity = Column("minimumOrderQuantity", Integer, nullable=False)
    meta = Column(JSON, nullable=False)
    images = Column(JSON, nullable=False)
    thumbnail = Column(String, nullable=False)

    is_featured = Column(Boolean, default=False, server_default="false", index=True)

    category_rel = relationship("Category", lazy="joined")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan", lazy="select")
    wishlist_items = relationship("WishlistItem", back_populates="product", cascade="all, delete-orphan")

    @property
    def category(self):
        return self.category_rel.name if self.category_rel else ""
