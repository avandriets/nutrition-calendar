from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_nutrition_average_and_timeline() -> None:
    account_id = client.post(
        "/accounts", json={"name": "Statistics test"}
    ).json()["id"]
    user_id = client.post(
        f"/accounts/{account_id}/users",
        json={"name": "User", "birth_date": None},
    ).json()["id"]
    product_id = client.post(
        "/products",
        json={
            "name": "Statistics product",
            "brand": None,
            "category": "Test",
            "barcode": None,
            "description": None,
            "calories_kcal": 100,
            "protein_g": 10,
            "fat_g": 5,
            "carbohydrates_g": 10,
            "fiber_g": 2,
        },
    ).json()["id"]

    for meal_date, amount in (("2026-02-01", 100), ("2026-02-03", 200)):
        meal_id = client.post(
            f"/accounts/{account_id}/meals",
            json={"meal_date": meal_date, "meal_type": "breakfast", "name": None},
        ).json()["id"]
        response = client.put(
            f"/accounts/{account_id}/meals/{meal_id}/entries",
            json={"user_id": user_id, "product_id": product_id, "amount_g": amount},
        )
        assert response.status_code == 200

    base_url = f"/accounts/{account_id}/users/{user_id}/statistics/nutrition"
    period = "date_from=2026-02-01&date_to=2026-02-03"

    average = client.get(f"{base_url}/average?{period}")
    assert average.status_code == 200
    assert average.json()["calendar_days"] == 3
    assert average.json()["active_days"] == 2
    assert average.json()["calories_kcal"] == 100
    assert average.json()["protein_g"] == 10
    assert average.json()["fat_g"] == 5
    assert average.json()["carbohydrates_g"] == 10
    assert average.json()["fiber_g"] == 2

    active_average = client.get(
        f"{base_url}/average?{period}&include_empty_days=false"
    )
    assert active_average.status_code == 200
    assert active_average.json()["calories_kcal"] == 150

    daily = client.get(f"{base_url}/timeline?{period}&granularity=day")
    assert daily.status_code == 200
    assert [point["calories_kcal"] for point in daily.json()["points"]] == [100, 0, 200]
    assert [point["active_days"] for point in daily.json()["points"]] == [1, 0, 1]

    weekly = client.get(f"{base_url}/timeline?{period}&granularity=week")
    assert weekly.status_code == 200
    assert len(weekly.json()["points"]) == 2
    assert [point["calories_kcal"] for point in weekly.json()["points"]] == [100, 100]

    invalid = client.get(
        f"{base_url}/average?date_from=2026-02-03&date_to=2026-02-01"
    )
    assert invalid.status_code == 422

    assert client.delete(f"/accounts/{account_id}").status_code == 204
    assert client.delete(f"/products/{product_id}").status_code == 204
