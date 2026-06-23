from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, BadRequestError, ConflictError
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import get_product_by_id


def create_product(db: Session, product_in: ProductCreate) -> Product:
    data = product_in.model_dump(exclude_none=True)
    if not db.query(Category).filter(Category.id == data.get("category_id")).first():
        raise BadRequestError(f"Category with id {data['category_id']} not found")
    try:
        product = Product(**data)
        db.add(product)
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise ConflictError("Product with this id or sku already exists")
    return product


def update_product(db: Session, product_id: int, product_in: ProductUpdate) -> Product:
    product = get_product_by_id(db, product_id)
    update_data = product_in.model_dump(exclude_unset=True)
    if "category_id" in update_data and not db.query(Category).filter(Category.id == update_data["category_id"]).first():
        raise BadRequestError(f"Category with id {update_data['category_id']} not found")
    for field, value in update_data.items():
        setattr(product, field, value)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise ConflictError("Update violates a unique constraint (id or sku)")
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product_by_id(db, product_id)
    db.delete(product)
    db.commit()
