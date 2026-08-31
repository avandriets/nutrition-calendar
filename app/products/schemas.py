from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    brand: Optional[str] = Field(default=None, max_length=200)
    category: Optional[str] = Field(default=None, max_length=100)
    barcode: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = None

    calories_kcal: float = Field(ge=0, description="Ккал на 100 г")
    protein_g: float = Field(ge=0, description="Белки на 100 г")
    fat_g: float = Field(ge=0, description="Жиры на 100 г")
    carbohydrates_g: float = Field(ge=0, description="Углеводы на 100 г")
    fiber_g: float = Field(ge=0, description="Клетчатка на 100 г")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
