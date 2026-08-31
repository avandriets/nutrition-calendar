from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.products import service
from app.products.model import Product
from app.products.schemas import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def get_product_or_404(product_id: int, db: Session) -> Product:
    product = service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def raise_duplicate_barcode() -> None:
    raise HTTPException(status_code=409, detail="Product barcode already exists")


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    try:
        return service.create_product(db, payload.model_dump())
    except service.DuplicateProductBarcodeError:
        raise_duplicate_barcode()


@router.get("", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[Product]:
    return service.list_products(db, skip, limit)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    return get_product_or_404(product_id, db)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> Product:
    product = get_product_or_404(product_id, db)
    try:
        return service.update_product(db, product, payload.model_dump())
    except service.DuplicateProductBarcodeError:
        raise_duplicate_barcode()


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> Response:
    product = get_product_or_404(product_id, db)
    service.delete_product(db, product)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
