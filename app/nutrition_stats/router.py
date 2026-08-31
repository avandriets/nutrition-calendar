from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.nutrition_stats import service
from app.nutrition_stats.schemas import (
    NutritionAverageResponse,
    NutritionTimelineResponse,
    TimelineGranularity,
)
from app.users.router import get_user_or_404

router = APIRouter(
    prefix="/accounts/{account_id}/users/{user_id}/statistics/nutrition",
    tags=["nutrition statistics"],
)


def validate_period(date_from: date, date_to: date) -> None:
    if date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")
    if (date_to - date_from).days > 3660:
        raise HTTPException(status_code=422, detail="The period cannot exceed 10 years")


@router.get("/average", response_model=NutritionAverageResponse)
def get_nutrition_average(
    account_id: int,
    user_id: int,
    date_from: date,
    date_to: date,
    include_empty_days: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> NutritionAverageResponse:
    validate_period(date_from, date_to)
    get_user_or_404(account_id, user_id, db)
    daily = service.get_daily_totals(db, account_id, user_id, date_from, date_to)
    calendar_days, active_days, values = service.calculate_average(
        daily, date_from, date_to, include_empty_days
    )
    return NutritionAverageResponse(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        calendar_days=calendar_days,
        active_days=active_days,
        include_empty_days=include_empty_days,
        **values,
    )


@router.get("/timeline", response_model=NutritionTimelineResponse)
def get_nutrition_timeline(
    account_id: int,
    user_id: int,
    date_from: date,
    date_to: date,
    granularity: TimelineGranularity = Query(default=TimelineGranularity.day),
    include_empty_days: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> NutritionTimelineResponse:
    validate_period(date_from, date_to)
    get_user_or_404(account_id, user_id, db)
    daily = service.get_daily_totals(db, account_id, user_id, date_from, date_to)
    return NutritionTimelineResponse(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        granularity=granularity,
        include_empty_days=include_empty_days,
        points=service.calculate_timeline(
            daily,
            date_from,
            date_to,
            granularity,
            include_empty_days,
        ),
    )
