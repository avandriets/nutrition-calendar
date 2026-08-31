from datetime import date, timedelta
from typing import Dict, Iterable, List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.meals.model import Meal, MealEntry, MealRow
from app.nutrition_stats.schemas import TimelineGranularity

NUTRIENT_FIELDS = (
    "calories_kcal",
    "protein_g",
    "fat_g",
    "carbohydrates_g",
    "fiber_g",
)


def empty_values() -> Dict[str, float]:
    return {field: 0.0 for field in NUTRIENT_FIELDS}


def round_values(values: Dict[str, float]) -> Dict[str, float]:
    return {field: round(values[field], 3) for field in NUTRIENT_FIELDS}


def date_range(date_from: date, date_to: date) -> Iterable[date]:
    current = date_from
    while current <= date_to:
        yield current
        current += timedelta(days=1)


def get_daily_totals(
    db: Session,
    account_id: int,
    user_id: int,
    date_from: date,
    date_to: date,
) -> Dict[date, Dict[str, float]]:
    rows = (
        db.query(
            Meal.meal_date,
            func.sum(MealRow.calories_kcal * MealEntry.amount_g / 100.0),
            func.sum(MealRow.protein_g * MealEntry.amount_g / 100.0),
            func.sum(MealRow.fat_g * MealEntry.amount_g / 100.0),
            func.sum(MealRow.carbohydrates_g * MealEntry.amount_g / 100.0),
            func.sum(MealRow.fiber_g * MealEntry.amount_g / 100.0),
        )
        .select_from(MealEntry)
        .join(MealRow, MealEntry.meal_row_id == MealRow.id)
        .join(Meal, MealRow.meal_id == Meal.id)
        .filter(
            Meal.account_id == account_id,
            MealEntry.user_id == user_id,
            Meal.meal_date >= date_from,
            Meal.meal_date <= date_to,
        )
        .group_by(Meal.meal_date)
        .order_by(Meal.meal_date)
        .all()
    )
    return {
        row[0]: {
            field: float(row[index] or 0)
            for index, field in enumerate(NUTRIENT_FIELDS, start=1)
        }
        for row in rows
    }


def calculate_average(
    daily_totals: Dict[date, Dict[str, float]],
    date_from: date,
    date_to: date,
    include_empty_days: bool,
) -> Tuple[int, int, Dict[str, float]]:
    calendar_days = (date_to - date_from).days + 1
    active_days = len(daily_totals)
    denominator = calendar_days if include_empty_days else active_days
    totals = empty_values()
    for values in daily_totals.values():
        for field in NUTRIENT_FIELDS:
            totals[field] += values[field]
    if denominator:
        totals = {field: value / denominator for field, value in totals.items()}
    return calendar_days, active_days, round_values(totals)


def bucket_start(value: date, granularity: TimelineGranularity) -> date:
    if granularity == TimelineGranularity.day:
        return value
    if granularity == TimelineGranularity.week:
        return value - timedelta(days=value.weekday())
    return value.replace(day=1)


def bucket_end(value: date, granularity: TimelineGranularity) -> date:
    if granularity == TimelineGranularity.day:
        return value
    if granularity == TimelineGranularity.week:
        return value + timedelta(days=6)
    next_month = (
        value.replace(year=value.year + 1, month=1, day=1)
        if value.month == 12
        else value.replace(month=value.month + 1, day=1)
    )
    return next_month - timedelta(days=1)


def calculate_timeline(
    daily_totals: Dict[date, Dict[str, float]],
    date_from: date,
    date_to: date,
    granularity: TimelineGranularity,
    include_empty_days: bool,
) -> List[Dict[str, object]]:
    days = list(date_range(date_from, date_to)) if include_empty_days else sorted(daily_totals)
    buckets: Dict[date, Dict[str, object]] = {}
    for day in days:
        start = bucket_start(day, granularity)
        bucket = buckets.setdefault(start, {"totals": empty_values(), "active_days": 0})
        values = daily_totals.get(day)
        if values is not None:
            bucket["active_days"] += 1
            for field in NUTRIENT_FIELDS:
                bucket["totals"][field] += values[field]

    points = []
    for natural_start, bucket in sorted(buckets.items()):
        start = max(natural_start, date_from)
        end = min(bucket_end(natural_start, granularity), date_to)
        calendar_days = (end - start).days + 1
        active_days = bucket["active_days"]
        denominator = calendar_days if include_empty_days else active_days
        values = bucket["totals"]
        if denominator:
            values = {field: values[field] / denominator for field in NUTRIENT_FIELDS}
        points.append({
            "period_start": start,
            "period_end": end,
            "calendar_days": calendar_days,
            "active_days": active_days,
            **round_values(values),
        })
    return points
