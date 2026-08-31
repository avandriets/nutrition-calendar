from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    other = "other"


class MealBase(BaseModel):
    meal_date: date
    meal_type: MealType
    name: Optional[str] = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_custom_name(self):
        if self.meal_type == MealType.other and not self.name:
            raise ValueError("A name is required for an 'other' meal")
        return self


class MealCreate(MealBase):
    pass


class MealUpdate(MealBase):
    pass


class PortionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount_g: float
    version: int
    created_at: datetime
    updated_at: datetime


class MealRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    product_id: Optional[int]
    product_name: str
    product_brand: Optional[str]
    calories_kcal: float
    protein_g: float
    fat_g: float
    carbohydrates_g: float
    fiber_g: float
    portions: List[PortionResponse]


class MealResponse(MealBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    created_at: datetime
    updated_at: datetime
    rows: List[MealRowResponse]


class MealEntryUpsert(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    amount_g: float = Field(gt=0)
    version: Optional[int] = Field(default=None, ge=1)


class MealEntryBatchUpsert(BaseModel):
    entries: List[MealEntryUpsert] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def reject_duplicate_cells(self):
        cells = [(entry.user_id, entry.product_id) for entry in self.entries]
        if len(cells) != len(set(cells)):
            raise ValueError("The batch contains duplicate user/product cells")
        return self


class EntryResponse(PortionResponse):
    meal_row_id: int
    product_id: Optional[int]
    position: int


class EntryBatchResponse(BaseModel):
    entries: List[EntryResponse]


class RowOrderUpdate(BaseModel):
    row_ids: List[int] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_rows(self):
        if len(self.row_ids) != len(set(self.row_ids)):
            raise ValueError("row_ids must be unique")
        return self


class MealDayResponse(BaseModel):
    account_id: int
    meal_date: date
    meals: List[MealResponse]


class MealDayCopyRequest(BaseModel):
    source_date: date
    replace_existing: bool = False


class UserDailyTotal(BaseModel):
    user_id: int
    calories_kcal: float
    protein_g: float
    fat_g: float
    carbohydrates_g: float
    fiber_g: float


class MealDayTotalsResponse(BaseModel):
    account_id: int
    meal_date: date
    users: List[UserDailyTotal]
