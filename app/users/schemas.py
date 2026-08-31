from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    birth_date: Optional[date] = None
    height_cm: Optional[float] = Field(default=None, gt=0, le=300)


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    created_at: datetime
    updated_at: datetime


class GoalBase(BaseModel):
    daily_calories_kcal: float = Field(gt=0)
    daily_protein_g: float = Field(ge=0)
    daily_fiber_g: float = Field(ge=0)
    effective_from: date = Field(default_factory=date.today)


class GoalCreate(GoalBase):
    pass


class GoalUpdate(GoalBase):
    pass


class GoalResponse(GoalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class GoalTimelineItem(GoalBase):
    goal_id: int
    period_start: date
    period_end: date


class GoalTimelineResponse(BaseModel):
    user_id: int
    date_from: date
    date_to: date
    periods: list[GoalTimelineItem]


class MeasurementBase(BaseModel):
    measured_on: date = Field(default_factory=date.today)
    weight_kg: Optional[float] = Field(default=None, gt=0)
    neck_cm: Optional[float] = Field(default=None, gt=0)
    waist_cm: Optional[float] = Field(default=None, gt=0)
    hips_cm: Optional[float] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_at_least_one_measurement(self):
        values = (self.weight_kg, self.neck_cm, self.waist_cm, self.hips_cm)
        if all(value is None for value in values):
            raise ValueError("At least one body measurement is required")
        return self


class MeasurementCreate(MeasurementBase):
    pass


class MeasurementUpdate(MeasurementBase):
    pass


class MeasurementResponse(MeasurementBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
