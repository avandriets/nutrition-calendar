from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.meals.model import Meal, MealEntry, MealRow
from app.meals.schemas import MealCreate, MealEntryUpsert, MealType, MealUpdate
from app.products.model import Product
from app.users.model import AccountUser


class MealConflictError(Exception):
    pass


class EntryVersionConflictError(Exception):
    pass


class RelatedEntityNotFoundError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class SourceMealDayNotFoundError(Exception):
    pass


class TargetMealDayNotEmptyError(Exception):
    pass


class SameMealDayError(Exception):
    pass


def _standard_meal_exists(
    db: Session,
    account_id: int,
    meal_date: date,
    meal_type: MealType,
    exclude_id: Optional[int] = None,
) -> bool:
    if meal_type == MealType.other:
        return False
    query = db.query(Meal).filter(
        Meal.account_id == account_id,
        Meal.meal_date == meal_date,
        Meal.meal_type == meal_type.value,
    )
    if exclude_id is not None:
        query = query.filter(Meal.id != exclude_id)
    return query.first() is not None


def create_meal(db: Session, account_id: int, payload: MealCreate) -> Meal:
    if _standard_meal_exists(db, account_id, payload.meal_date, payload.meal_type):
        raise MealConflictError
    data = payload.model_dump()
    data["meal_type"] = payload.meal_type.value
    meal = Meal(account_id=account_id, **data)
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


def list_meals(db: Session, account_id: int, meal_date: Optional[date] = None) -> List[Meal]:
    query = db.query(Meal).filter(Meal.account_id == account_id)
    if meal_date is not None:
        query = query.filter(Meal.meal_date == meal_date)
    return query.order_by(Meal.meal_date, Meal.created_at, Meal.id).all()


def get_meal(db: Session, account_id: int, meal_id: int) -> Optional[Meal]:
    return db.query(Meal).filter(Meal.account_id == account_id, Meal.id == meal_id).first()


def update_meal(db: Session, meal: Meal, payload: MealUpdate) -> Meal:
    if _standard_meal_exists(
        db,
        meal.account_id,
        payload.meal_date,
        payload.meal_type,
        exclude_id=meal.id,
    ):
        raise MealConflictError
    data = payload.model_dump()
    data["meal_type"] = payload.meal_type.value
    for field, value in data.items():
        setattr(meal, field, value)
    db.commit()
    db.refresh(meal)
    return meal


def delete_meal(db: Session, meal: Meal) -> None:
    db.delete(meal)
    db.commit()


def _load_related_entities(
    db: Session,
    account_id: int,
    entries: Sequence[MealEntryUpsert],
) -> Tuple[Dict[int, AccountUser], Dict[int, Product]]:
    user_ids = {entry.user_id for entry in entries}
    product_ids = {entry.product_id for entry in entries}
    users = db.query(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.id.in_(user_ids),
    ).all()
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    users_by_id = {user.id: user for user in users}
    products_by_id = {product.id: product for product in products}
    missing_users = sorted(user_ids - set(users_by_id))
    missing_products = sorted(product_ids - set(products_by_id))
    if missing_users:
        raise RelatedEntityNotFoundError(f"Users not found in this account: {missing_users}")
    if missing_products:
        raise RelatedEntityNotFoundError(f"Products not found: {missing_products}")
    return users_by_id, products_by_id


def upsert_entries(
    db: Session,
    meal: Meal,
    payloads: Sequence[MealEntryUpsert],
) -> List[MealEntry]:
    _, products = _load_related_entities(db, meal.account_id, payloads)
    product_ids = {payload.product_id for payload in payloads}
    rows = db.query(MealRow).filter(
        MealRow.meal_id == meal.id,
        MealRow.product_id.in_(product_ids),
    ).all()
    rows_by_product = {row.product_id: row for row in rows}
    next_position = db.query(func.coalesce(func.max(MealRow.position), 0)).filter(
        MealRow.meal_id == meal.id
    ).scalar()

    for payload in payloads:
        if payload.product_id not in rows_by_product:
            product = products[payload.product_id]
            next_position += 1
            row = MealRow(
                meal_id=meal.id,
                product_id=product.id,
                position=next_position,
                product_name=product.name,
                product_brand=product.brand,
                calories_kcal=product.calories_kcal,
                protein_g=product.protein_g,
                fat_g=product.fat_g,
                carbohydrates_g=product.carbohydrates_g,
                fiber_g=product.fiber_g,
            )
            db.add(row)
            rows_by_product[product.id] = row
    db.flush()

    row_ids = [row.id for row in rows_by_product.values()]
    user_ids = {payload.user_id for payload in payloads}
    existing = db.query(MealEntry).filter(
        MealEntry.meal_row_id.in_(row_ids),
        MealEntry.user_id.in_(user_ids),
    ).all()
    entries_by_cell = {(entry.meal_row_id, entry.user_id): entry for entry in existing}
    saved = []
    for payload in payloads:
        row = rows_by_product[payload.product_id]
        cell = (row.id, payload.user_id)
        entry = entries_by_cell.get(cell)
        if entry is None:
            entry = MealEntry(
                meal_row_id=row.id,
                user_id=payload.user_id,
                amount_g=payload.amount_g,
            )
            db.add(entry)
            entries_by_cell[cell] = entry
        else:
            if payload.version is not None and payload.version != entry.version:
                db.rollback()
                raise EntryVersionConflictError
            entry.amount_g = payload.amount_g
        saved.append(entry)

    try:
        db.commit()
    except StaleDataError as exc:
        db.rollback()
        raise EntryVersionConflictError from exc
    except IntegrityError as exc:
        db.rollback()
        raise MealConflictError from exc
    for entry in saved:
        db.refresh(entry)
    return saved


def delete_entry(db: Session, entry: MealEntry) -> None:
    row = entry.row
    db.delete(entry)
    db.flush()
    remaining = db.query(MealEntry).filter(MealEntry.meal_row_id == row.id).count()
    if remaining == 0:
        db.delete(row)
    db.commit()


def get_entry(db: Session, meal_id: int, entry_id: int) -> Optional[MealEntry]:
    return db.query(MealEntry).join(MealRow).filter(
        MealRow.meal_id == meal_id,
        MealEntry.id == entry_id,
    ).first()


def reorder_rows(db: Session, meal: Meal, row_ids: List[int]) -> Meal:
    rows = db.query(MealRow).filter(MealRow.meal_id == meal.id).all()
    rows_by_id = {row.id: row for row in rows}
    if set(row_ids) != set(rows_by_id):
        raise RelatedEntityNotFoundError("row_ids must contain every row of the meal")
    for index, row_id in enumerate(row_ids, start=1):
        rows_by_id[row_id].position = -index
    db.flush()
    for index, row_id in enumerate(row_ids, start=1):
        rows_by_id[row_id].position = index
    db.commit()
    db.refresh(meal)
    return meal


def calculate_daily_totals(meals: Sequence[Meal]) -> List[Dict[str, float]]:
    totals: Dict[int, Dict[str, float]] = {}
    for meal in meals:
        for row in meal.rows:
            for portion in row.portions:
                user_total = totals.setdefault(
                    portion.user_id,
                    {
                        "user_id": portion.user_id,
                        "calories_kcal": 0.0,
                        "protein_g": 0.0,
                        "fat_g": 0.0,
                        "carbohydrates_g": 0.0,
                        "fiber_g": 0.0,
                    },
                )
                factor = portion.amount_g / 100
                for field in (
                    "calories_kcal",
                    "protein_g",
                    "fat_g",
                    "carbohydrates_g",
                    "fiber_g",
                ):
                    user_total[field] += getattr(row, field) * factor
    for user_total in totals.values():
        for field, value in user_total.items():
            if field != "user_id":
                user_total[field] = round(value, 3)
    return [totals[user_id] for user_id in sorted(totals)]


def copy_meal_day(
    db: Session,
    account_id: int,
    target_date: date,
    source_date: date,
    replace_existing: bool = False,
) -> List[Meal]:
    if source_date == target_date:
        raise SameMealDayError

    source_meals = list_meals(db, account_id, source_date)
    if not source_meals:
        raise SourceMealDayNotFoundError

    target_meals = list_meals(db, account_id, target_date)
    if target_meals and not replace_existing:
        raise TargetMealDayNotEmptyError

    if replace_existing:
        for meal in target_meals:
            db.delete(meal)
        db.flush()

    for source_meal in source_meals:
        new_meal = Meal(
            account_id=account_id,
            meal_date=target_date,
            meal_type=source_meal.meal_type,
            name=source_meal.name,
        )
        for source_row in source_meal.rows:
            new_row = MealRow(
                product_id=source_row.product_id,
                position=source_row.position,
                product_name=source_row.product_name,
                product_brand=source_row.product_brand,
                calories_kcal=source_row.calories_kcal,
                protein_g=source_row.protein_g,
                fat_g=source_row.fat_g,
                carbohydrates_g=source_row.carbohydrates_g,
                fiber_g=source_row.fiber_g,
            )
            for source_portion in source_row.portions:
                new_row.portions.append(
                    MealEntry(
                        user_id=source_portion.user_id,
                        amount_g=source_portion.amount_g,
                        version=1,
                    )
                )
            new_meal.rows.append(new_row)
        db.add(new_meal)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    return list_meals(db, account_id, target_date)
