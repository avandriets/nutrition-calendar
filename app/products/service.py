from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.products.model import Product


class DuplicateProductBarcodeError(Exception):
    """Raised when another product already has the supplied barcode."""


def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def list_products(db: Session, skip: int, limit: int) -> List[Product]:
    return db.query(Product).order_by(Product.id).offset(skip).limit(limit).all()


def save_product(db: Session, product: Product) -> Product:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateProductBarcodeError from exc
    db.refresh(product)
    return product


def create_product(db: Session, data: Dict[str, Any]) -> Product:
    product = Product(**data)
    db.add(product)
    return save_product(db, product)


def update_product(db: Session, product: Product, data: Dict[str, Any]) -> Product:
    for field, value in data.items():
        setattr(product, field, value)
    return save_product(db, product)


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()
