from datetime import date

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_product(name: str, calories: float) -> int:
    response = client.post(
        "/products",
        json={
            "name": name,
            "brand": None,
            "category": "Test",
            "barcode": None,
            "description": None,
            "calories_kcal": calories,
            "protein_g": 10,
            "fat_g": 5,
            "carbohydrates_g": 20,
            "fiber_g": 4,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_family_meal_single_batch_order_versions_and_totals() -> None:
    account = client.post("/accounts", json={"name": "Meal test family"}).json()
    account_id = account["id"]
    user_ids = []
    for name in ("Анна", "Олег"):
        response = client.post(
            f"/accounts/{account_id}/users",
            json={"name": name, "birth_date": None},
        )
        assert response.status_code == 201
        user_ids.append(response.json()["id"])

    oatmeal_id = create_product("Овсянка", 370)
    banana_id = create_product("Банан", 90)
    today = date.today().isoformat()
    meal_response = client.post(
        f"/accounts/{account_id}/meals",
        json={"meal_date": today, "meal_type": "breakfast", "name": None},
    )
    assert meal_response.status_code == 201
    meal_id = meal_response.json()["id"]

    single = client.put(
        f"/accounts/{account_id}/meals/{meal_id}/entries",
        json={"user_id": user_ids[0], "product_id": oatmeal_id, "amount_g": 100},
    )
    assert single.status_code == 200
    assert single.json()["version"] == 1

    batch = client.put(
        f"/accounts/{account_id}/meals/{meal_id}/entries/batch",
        json={
            "entries": [
                {"user_id": user_ids[1], "product_id": oatmeal_id, "amount_g": 150},
                {"user_id": user_ids[0], "product_id": banana_id, "amount_g": 120},
                {"user_id": user_ids[1], "product_id": banana_id, "amount_g": 80},
            ]
        },
    )
    assert batch.status_code == 200
    assert len(batch.json()["entries"]) == 3

    meal = client.get(f"/accounts/{account_id}/meals/{meal_id}")
    assert meal.status_code == 200
    rows = meal.json()["rows"]
    assert [row["product_name"] for row in rows] == ["Овсянка", "Банан"]
    assert len(rows[0]["portions"]) == 2

    current_entry = single.json()
    updated = client.put(
        f"/accounts/{account_id}/meals/{meal_id}/entries",
        json={
            "user_id": user_ids[0],
            "product_id": oatmeal_id,
            "amount_g": 110,
            "version": current_entry["version"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2

    stale = client.put(
        f"/accounts/{account_id}/meals/{meal_id}/entries",
        json={
            "user_id": user_ids[0],
            "product_id": oatmeal_id,
            "amount_g": 115,
            "version": 1,
        },
    )
    assert stale.status_code == 409

    reordered = client.put(
        f"/accounts/{account_id}/meals/{meal_id}/rows/order",
        json={"row_ids": [rows[1]["id"], rows[0]["id"]]},
    )
    assert reordered.status_code == 200
    assert [row["product_name"] for row in reordered.json()["rows"]] == ["Банан", "Овсянка"]

    day = client.get(f"/accounts/{account_id}/meal-days/{today}")
    assert day.status_code == 200
    assert len(day.json()["meals"]) == 1

    totals = client.get(f"/accounts/{account_id}/meal-days/{today}/totals")
    assert totals.status_code == 200
    totals_by_user = {item["user_id"]: item for item in totals.json()["users"]}
    assert totals_by_user[user_ids[0]]["calories_kcal"] == 515.0
    assert totals_by_user[user_ids[1]]["calories_kcal"] == 627.0

    assert client.delete(f"/accounts/{account_id}").status_code == 204
    assert client.delete(f"/products/{oatmeal_id}").status_code == 204
    assert client.delete(f"/products/{banana_id}").status_code == 204


def test_other_meal_requires_name() -> None:
    account_id = client.post("/accounts", json={"name": "Other meal test"}).json()["id"]
    response = client.post(
        f"/accounts/{account_id}/meals",
        json={"meal_date": date.today().isoformat(), "meal_type": "other", "name": None},
    )
    assert response.status_code == 422
    assert client.delete(f"/accounts/{account_id}").status_code == 204


def test_copy_previous_meal_day_as_template() -> None:
    account_id = client.post(
        "/accounts", json={"name": "Meal copy test"}
    ).json()["id"]
    user_id = client.post(
        f"/accounts/{account_id}/users",
        json={"name": "User", "birth_date": None},
    ).json()["id"]
    product_id = create_product("Copy product", 200)

    source_date = "2026-01-10"
    target_date = "2026-01-11"
    meal = client.post(
        f"/accounts/{account_id}/meals",
        json={"meal_date": source_date, "meal_type": "breakfast", "name": None},
    ).json()
    entry = client.put(
        f"/accounts/{account_id}/meals/{meal['id']}/entries",
        json={"user_id": user_id, "product_id": product_id, "amount_g": 175},
    )
    assert entry.status_code == 200

    copied = client.post(
        f"/accounts/{account_id}/meal-days/{target_date}/copy",
        json={"source_date": source_date},
    )
    assert copied.status_code == 201
    copied_meals = copied.json()["meals"]
    assert len(copied_meals) == 1
    assert copied_meals[0]["meal_date"] == target_date
    assert copied_meals[0]["rows"][0]["product_name"] == "Copy product"
    copied_portion = copied_meals[0]["rows"][0]["portions"][0]
    assert copied_portion["amount_g"] == 175
    assert copied_portion["version"] == 1

    conflict = client.post(
        f"/accounts/{account_id}/meal-days/{target_date}/copy",
        json={"source_date": source_date},
    )
    assert conflict.status_code == 409

    missing_source_date = client.post(
        f"/accounts/{account_id}/meal-days/2026-01-12/copy",
        json={},
    )
    assert missing_source_date.status_code == 422

    replaced = client.post(
        f"/accounts/{account_id}/meal-days/{target_date}/copy",
        json={"source_date": source_date, "replace_existing": True},
    )
    assert replaced.status_code == 201
    assert len(replaced.json()["meals"]) == 1

    assert client.delete(f"/accounts/{account_id}").status_code == 204
    assert client.delete(f"/products/{product_id}").status_code == 204
