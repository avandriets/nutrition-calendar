"""Import the legacy family food diary CSV into the normalized meal tables."""

import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Tuple

from app.accounts.model import Account
from app.database import SessionLocal
from app.meals import service
from app.meals.model import Meal, MealRow
from app.meals.schemas import MealCreate, MealEntryUpsert, MealType
from app.products.model import Product
from app.users.model import AccountUser


ACCOUNT_NAME = "Наша семья"
USER_NAMES = {"Саша": "Саша", "Оля": "Оля"}
SOURCE_DATE_CORRECTIONS = {
    "Калорийность - Sheet2.csv": {
        527: date(2026, 6, 5),
    },
    "Калорийность - Sheet1.csv": {
        2708: date(2025, 11, 11),
        3570: date(2025, 11, 20),
        14927: date(2026, 3, 15),
        15053: date(2026, 3, 16),
        15815: date(2026, 3, 29),
        19533: date(2026, 4, 27),
        19662: date(2026, 4, 28),
    },
}
SECTION_TYPES = {
    "Завтрак": (MealType.breakfast, None),
    "Перекус": (MealType.other, "Перекус"),
    "Обед": (MealType.lunch, None),
    "Ужин": (MealType.dinner, None),
}
PRODUCT_ALIASES = {
    "Барабулька": "Рыба барабулька",
    "Голубики": "Голубика",
    "Колбаса из индюшки": "Колбаса индюшинная с протеином",
    "Котлеты индюшинные": "Фарш индюшиный",
    "Курица грудка": "Куринная грудка",
    "Курица запеченая": "Курица запеченная",
    "Майонез обезжиренный": "Майонез обежиренный",
    "Напиток протеиновый": "Напиток протеиновый LIDL",
    "Пиво гиннес": "Пиво гинесс",
    "Рыба сибас": "Рыба сибас/Дорадо",
    "Сыр горгонзола": "Гарганзола",
    "масло оливковое": "Оливковое масло",
    "Yougurt": "Йогурт с протеином",
    "Fibra": "Отруби пшеничные Fibra",
    "GAUDA": "GAUDA старый",
    "Конские бобы": "Бобы",
    "Крабовые": "Крабовые палочки",
    "Креветки": "Лангустины",
    "Ногодняя конфета": "Конфета НОВОГОДНЯЯ",
    "Отруби интегральные овс": "Отруби овсянные Integral",
    "Рукола": "Руккола",
    "Скубмрия": "Скумбрия",
    "Скумбрия банка": "Скумбрия",
    "Стручковая фасоль": "стручковая фасоль",
    "Суфле": "Суфле птичье молоко",
    "Тунец банка": "Тунец в своем соку",
    "Утка заеченная": "Утка",
    "Чивевица": "Чичевица",
    "Шоколад": "Шоколад/Желе/Газировка",
    "Шоколад/Желе": "Шоколад/Желе/Газировка",
    "Яйцо": "Яйца",
    "баклажаны": "Баклажаны",
    "лук": "Лук",
}


@dataclass
class ImportedCell:
    meal_date: date
    section: str
    source_user: str
    source_product: str
    amount_g: float = 0
    calories: float = 0
    protein_g: float = 0
    fiber_g: float = 0


def number(value: str) -> float:
    value = value.strip().replace(",", ".")
    if not value:
        return 0.0
    if re.fullmatch(r"\d+(?:\.\d+)?(?:\+\d+(?:\.\d+)?)+", value):
        return sum(float(part) for part in value.split("+"))
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_csv(path: Path) -> List[ImportedCell]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.reader(source))

    date_corrections = SOURCE_DATE_CORRECTIONS.get(path.name, {})
    grouped: Dict[Tuple[date, str, str, str], ImportedCell] = {}
    current_date = None
    current_section = None
    for line_number, row in enumerate(rows, start=1):
        row = row + [""] * (15 - len(row))
        label = row[0].strip()
        try:
            parsed_date = datetime.strptime(label, "%d.%m.%Y").date()
        except ValueError:
            parsed_date = None
        if parsed_date is not None:
            current_date = date_corrections.get(line_number, parsed_date)
            current_section = None
            continue
        if label in SECTION_TYPES:
            current_section = label
            continue
        if current_date is None or current_section is None or not label or label == "Итог":
            continue

        for source_user, columns in {
            "Саша": (1, 2, 3, 4),
            "Оля": (5, 6, 7, 8),
        }.items():
            amount = number(row[columns[0]])
            if amount <= 0:
                continue
            key = (current_date, current_section, source_user, label)
            cell = grouped.setdefault(
                key,
                ImportedCell(current_date, current_section, source_user, label),
            )
            cell.amount_g += amount
            cell.calories += number(row[columns[1]])
            cell.protein_g += number(row[columns[2]])
            cell.fiber_g += number(row[columns[3]])
    return list(grouped.values())


def ensure_source_variants(db) -> None:
    variants = (
        {
            "name": "яблоко",
            "category": "Фрукты и ягоды",
            "calories_kcal": 79,
            "protein_g": 0,
            "fat_g": 0.3,
            "carbohydrates_g": 19.1,
            "fiber_g": 2,
        },
        {
            "name": "Шоколад/Желе/Газировка",
            "category": "Десерты",
            "calories_kcal": 500,
            "protein_g": 0,
            "fat_g": 25,
            "carbohydrates_g": 68.75,
            "fiber_g": 0,
        },
        {
            "name": "Авокадо", "category": "Фрукты и ягоды",
            "calories_kcal": 160, "protein_g": 2, "fat_g": 14.7,
            "carbohydrates_g": 8.5, "fiber_g": 6.7,
        },
        {
            "name": "Батончик", "category": "Спортивное питание",
            "calories_kcal": 325, "protein_g": 50, "fat_g": 5,
            "carbohydrates_g": 17, "fiber_g": 6.5,
        },
        {
            "name": "Кровянка", "category": "Мясо и птица",
            "calories_kcal": 320, "protein_g": 7, "fat_g": 29,
            "carbohydrates_g": 8, "fiber_g": 0,
        },
        {
            "name": "Лосось копченный", "category": "Рыба и морепродукты",
            "calories_kcal": 200, "protein_g": 20, "fat_g": 13.3,
            "carbohydrates_g": 0, "fiber_g": 0,
        },
        {
            "name": "Печенька", "category": "Десерты",
            "calories_kcal": 450, "protein_g": 8.75, "fat_g": 20,
            "carbohydrates_g": 58, "fiber_g": 2.583,
        },
        {
            "name": "Сливки", "category": "Молочные продукты и сыры",
            "calories_kcal": 163, "protein_g": 2.5, "fat_g": 15,
            "carbohydrates_g": 4, "fiber_g": 0,
        },
        {
            "name": "Суши", "category": "Готовые блюда и салаты",
            "calories_kcal": 149.877, "protein_g": 8.956, "fat_g": 3,
            "carbohydrates_g": 20, "fiber_g": 0.789,
        },
        {
            "name": "Сыр камамбер", "category": "Молочные продукты и сыры",
            "calories_kcal": 239.13, "protein_g": 17.391, "fat_g": 18.8,
            "carbohydrates_g": 0.5, "fiber_g": 0,
        },
        {
            "name": "Чилетон", "category": "Мясо и птица",
            "calories_kcal": 250, "protein_g": 24, "fat_g": 17,
            "carbohydrates_g": 0, "fiber_g": 0,
        },
        {
            "name": "Чиперон", "category": "Рыба и морепродукты",
            "calories_kcal": 391.429, "protein_g": 20.571, "fat_g": 30,
            "carbohydrates_g": 8, "fiber_g": 0,
        },
    )
    for data in variants:
        exists = db.query(Product).filter(
            Product.name == data["name"],
            Product.calories_kcal == data["calories_kcal"],
        ).first()
        if exists is None:
            db.add(Product(
                **data,
                description="Добавлено при импорте исторического дневника питания",
            ))
    db.commit()


def product_observations(cells: Iterable[ImportedCell]) -> Dict[str, Tuple[float, float, float]]:
    totals: DefaultDict[str, List[float]] = defaultdict(lambda: [0, 0, 0, 0])
    for cell in cells:
        values = totals[cell.source_product]
        values[0] += cell.amount_g
        values[1] += cell.calories
        values[2] += cell.protein_g
        values[3] += cell.fiber_g
    return {
        name: (
            values[1] / values[0] * 100,
            values[2] / values[0] * 100,
            values[3] / values[0] * 100,
        )
        for name, values in totals.items()
    }


def resolve_products(db, cells: Iterable[ImportedCell]) -> Dict[str, Product]:
    observations = product_observations(cells)
    products = db.query(Product).all()
    by_name: DefaultDict[str, List[Product]] = defaultdict(list)
    for product in products:
        by_name[product.name.casefold()].append(product)

    resolved = {}
    for source_name, observed in observations.items():
        catalogue_name = PRODUCT_ALIASES.get(source_name, source_name)
        candidates = by_name[catalogue_name.casefold()]
        if not candidates:
            raise RuntimeError(f"Product not found: {source_name} -> {catalogue_name}")
        resolved[source_name] = min(
            candidates,
            key=lambda product: (
                abs(product.calories_kcal - observed[0])
                + abs(product.protein_g - observed[1])
                + abs(product.fiber_g - observed[2])
            ),
        )
    return resolved


def get_or_create_meal(db, account_id: int, meal_date: date, section: str) -> Meal:
    meal_type, name = SECTION_TYPES[section]
    query = db.query(Meal).filter(
        Meal.account_id == account_id,
        Meal.meal_date == meal_date,
        Meal.meal_type == meal_type.value,
    )
    if meal_type == MealType.other:
        query = query.filter(Meal.name == name)
    meal = query.first()
    if meal is not None:
        return meal
    return service.create_meal(
        db,
        account_id,
        MealCreate(meal_date=meal_date, meal_type=meal_type, name=name),
    )


def import_cells(path: Path) -> Tuple[int, int, int]:
    cells = parse_csv(path)
    db = SessionLocal()
    try:
        account = db.query(Account).filter(Account.name == ACCOUNT_NAME).one()
        users = {
            source_name: db.query(AccountUser).filter(
                AccountUser.account_id == account.id,
                AccountUser.name == database_name,
            ).one()
            for source_name, database_name in USER_NAMES.items()
        }
        ensure_source_variants(db)
        products = resolve_products(db, cells)
        by_meal: DefaultDict[Tuple[date, str], List[ImportedCell]] = defaultdict(list)
        for cell in cells:
            by_meal[(cell.meal_date, cell.section)].append(cell)

        saved_cells = 0
        for (meal_date, section), meal_cells in sorted(by_meal.items()):
            meal = get_or_create_meal(db, account.id, meal_date, section)
            combined: Dict[Tuple[int, int], ImportedCell] = {}
            row_totals: DefaultDict[int, List[float]] = defaultdict(lambda: [0, 0, 0, 0])
            for cell in meal_cells:
                user_id = users[cell.source_user].id
                product = products[cell.source_product]
                key = (user_id, product.id)
                if key in combined:
                    target = combined[key]
                    target.amount_g += cell.amount_g
                    target.calories += cell.calories
                    target.protein_g += cell.protein_g
                    target.fiber_g += cell.fiber_g
                else:
                    combined[key] = ImportedCell(
                        cell.meal_date,
                        cell.section,
                        cell.source_user,
                        cell.source_product,
                        cell.amount_g,
                        cell.calories,
                        cell.protein_g,
                        cell.fiber_g,
                    )
                totals = row_totals[product.id]
                totals[0] += cell.amount_g
                totals[1] += cell.calories
                totals[2] += cell.protein_g
                totals[3] += cell.fiber_g

            payloads = [
                MealEntryUpsert(
                    user_id=user_id,
                    product_id=product_id,
                    amount_g=cell.amount_g,
                )
                for (user_id, product_id), cell in combined.items()
            ]
            service.upsert_entries(db, meal, payloads)
            for product_id, totals in row_totals.items():
                row = db.query(MealRow).filter(
                    MealRow.meal_id == meal.id,
                    MealRow.product_id == product_id,
                ).one()
                if totals[1] > 0:
                    row.calories_kcal = totals[1] / totals[0] * 100
                    row.protein_g = totals[2] / totals[0] * 100
                    row.fiber_g = totals[3] / totals[0] * 100
            db.commit()
            saved_cells += len(combined)

        imported_dates = {cell.meal_date for cell in cells}
        return len(imported_dates), len(by_meal), saved_cells
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()
    days, meals, cells = import_cells(args.csv_path)
    print(f"Imported days: {days}; meals: {meals}; non-zero cells: {cells}")


if __name__ == "__main__":
    main()
