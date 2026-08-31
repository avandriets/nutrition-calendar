from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.accounts.router import get_account_or_404
from app.database import get_db
from app.meals import service
from app.meals.model import Meal, MealEntry
from app.meals.schemas import (
    EntryBatchResponse,
    EntryResponse,
    MealCreate,
    MealDayCopyRequest,
    MealDayResponse,
    MealDayTotalsResponse,
    MealEntryBatchUpsert,
    MealEntryUpsert,
    MealResponse,
    MealUpdate,
    RowOrderUpdate,
)

router = APIRouter(prefix="/accounts/{account_id}", tags=["meals"])


def get_meal_or_404(account_id: int, meal_id: int, db: Session) -> Meal:
    get_account_or_404(account_id, db)
    meal = service.get_meal(db, account_id, meal_id)
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal


def entry_response(entry: MealEntry) -> EntryResponse:
    return EntryResponse(
        id=entry.id,
        meal_row_id=entry.meal_row_id,
        user_id=entry.user_id,
        product_id=entry.row.product_id,
        position=entry.row.position,
        amount_g=entry.amount_g,
        version=entry.version,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def upsert_or_error(db: Session, meal: Meal, entries: List[MealEntryUpsert]) -> List[MealEntry]:
    try:
        return service.upsert_entries(db, meal, entries)
    except service.RelatedEntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail) from exc
    except service.EntryVersionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="The entry was changed by another client; reload and try again",
        ) from exc
    except service.MealConflictError as exc:
        raise HTTPException(status_code=409, detail="Meal data conflict") from exc


@router.post("/meals", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def create_meal(account_id: int, payload: MealCreate, db: Session = Depends(get_db)) -> Meal:
    get_account_or_404(account_id, db)
    try:
        return service.create_meal(db, account_id, payload)
    except service.MealConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="This standard meal already exists for the selected date",
        ) from exc


@router.get("/meals", response_model=List[MealResponse])
def list_meals(
    account_id: int,
    meal_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[Meal]:
    get_account_or_404(account_id, db)
    return service.list_meals(db, account_id, meal_date)


@router.get("/meals/{meal_id}", response_model=MealResponse)
def get_meal(account_id: int, meal_id: int, db: Session = Depends(get_db)) -> Meal:
    return get_meal_or_404(account_id, meal_id, db)


@router.put("/meals/{meal_id}", response_model=MealResponse)
def update_meal(
    account_id: int,
    meal_id: int,
    payload: MealUpdate,
    db: Session = Depends(get_db),
) -> Meal:
    meal = get_meal_or_404(account_id, meal_id, db)
    try:
        return service.update_meal(db, meal, payload)
    except service.MealConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="This standard meal already exists for the selected date",
        ) from exc


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(account_id: int, meal_id: int, db: Session = Depends(get_db)) -> Response:
    service.delete_meal(db, get_meal_or_404(account_id, meal_id, db))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/meals/{meal_id}/entries", response_model=EntryResponse)
def upsert_entry(
    account_id: int,
    meal_id: int,
    payload: MealEntryUpsert,
    db: Session = Depends(get_db),
) -> EntryResponse:
    meal = get_meal_or_404(account_id, meal_id, db)
    return entry_response(upsert_or_error(db, meal, [payload])[0])


@router.put("/meals/{meal_id}/entries/batch", response_model=EntryBatchResponse)
def upsert_entry_batch(
    account_id: int,
    meal_id: int,
    payload: MealEntryBatchUpsert,
    db: Session = Depends(get_db),
) -> EntryBatchResponse:
    meal = get_meal_or_404(account_id, meal_id, db)
    saved = upsert_or_error(db, meal, payload.entries)
    return EntryBatchResponse(entries=[entry_response(entry) for entry in saved])


@router.delete("/meals/{meal_id}/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    account_id: int,
    meal_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
) -> Response:
    meal = get_meal_or_404(account_id, meal_id, db)
    entry = service.get_entry(db, meal.id, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Meal entry not found")
    service.delete_entry(db, entry)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/meals/{meal_id}/rows/order", response_model=MealResponse)
def reorder_rows(
    account_id: int,
    meal_id: int,
    payload: RowOrderUpdate,
    db: Session = Depends(get_db),
) -> Meal:
    meal = get_meal_or_404(account_id, meal_id, db)
    try:
        return service.reorder_rows(db, meal, payload.row_ids)
    except service.RelatedEntityNotFoundError as exc:
        raise HTTPException(status_code=422, detail=exc.detail) from exc


@router.get("/meal-days/{meal_date}", response_model=MealDayResponse)
def get_meal_day(account_id: int, meal_date: date, db: Session = Depends(get_db)) -> MealDayResponse:
    get_account_or_404(account_id, db)
    meals = service.list_meals(db, account_id, meal_date)
    return MealDayResponse(account_id=account_id, meal_date=meal_date, meals=meals)


@router.get("/meal-days/{meal_date}/totals", response_model=MealDayTotalsResponse)
def get_meal_day_totals(
    account_id: int,
    meal_date: date,
    db: Session = Depends(get_db),
) -> MealDayTotalsResponse:
    get_account_or_404(account_id, db)
    meals = service.list_meals(db, account_id, meal_date)
    return MealDayTotalsResponse(
        account_id=account_id,
        meal_date=meal_date,
        users=service.calculate_daily_totals(meals),
    )


@router.post(
    "/meal-days/{target_date}/copy",
    response_model=MealDayResponse,
    status_code=status.HTTP_201_CREATED,
)
def copy_meal_day(
    account_id: int,
    target_date: date,
    payload: MealDayCopyRequest,
    db: Session = Depends(get_db),
) -> MealDayResponse:
    get_account_or_404(account_id, db)
    try:
        meals = service.copy_meal_day(
            db,
            account_id,
            target_date,
            source_date=payload.source_date,
            replace_existing=payload.replace_existing,
        )
    except service.SourceMealDayNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source meal day not found") from exc
    except service.TargetMealDayNotEmptyError as exc:
        raise HTTPException(
            status_code=409,
            detail="Target meal day is not empty; use replace_existing=true to replace it",
        ) from exc
    except service.SameMealDayError as exc:
        raise HTTPException(
            status_code=422,
            detail="Source and target dates must be different",
        ) from exc
    return MealDayResponse(account_id=account_id, meal_date=target_date, meals=meals)
