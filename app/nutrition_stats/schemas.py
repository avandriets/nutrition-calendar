from datetime import date
from enum import Enum
from typing import List

from pydantic import BaseModel


class TimelineGranularity(str, Enum):
    day = "day"
    week = "week"
    month = "month"


class NutritionValues(BaseModel):
    calories_kcal: float
    protein_g: float
    fat_g: float
    carbohydrates_g: float
    fiber_g: float


class NutritionAverageResponse(NutritionValues):
    user_id: int
    date_from: date
    date_to: date
    calendar_days: int
    active_days: int
    include_empty_days: bool


class NutritionTimelinePoint(NutritionValues):
    period_start: date
    period_end: date
    calendar_days: int
    active_days: int


class NutritionTimelineResponse(BaseModel):
    user_id: int
    date_from: date
    date_to: date
    granularity: TimelineGranularity
    include_empty_days: bool
    points: List[NutritionTimelinePoint]
