from datetime import date

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_account_user_goal_and_measurement_lifecycle() -> None:
    account = client.post("/accounts", json={"name": "Семья Ивановых"})
    assert account.status_code == 201
    account_id = account.json()["id"]

    updated_account = client.put(
        f"/accounts/{account_id}",
        json={"name": "Наша семья"},
    )
    assert updated_account.status_code == 200
    assert updated_account.json()["name"] == "Наша семья"

    user = client.post(
        f"/accounts/{account_id}/users",
        json={"name": "Анна", "birth_date": "1990-05-15", "height_cm": 168},
    )
    assert user.status_code == 201
    assert user.json()["height_cm"] == 168
    user_id = user.json()["id"]

    goal_payload = {
        "daily_calories_kcal": 1800,
        "daily_protein_g": 100,
        "daily_fiber_g": 30,
        "effective_from": date.today().isoformat(),
    }
    goal = client.post(
        f"/accounts/{account_id}/users/{user_id}/goals",
        json=goal_payload,
    )
    assert goal.status_code == 201
    assert goal.json()["daily_protein_g"] == 100

    current_goal = client.get(
        f"/accounts/{account_id}/users/{user_id}/goals/current"
    )
    assert current_goal.status_code == 200
    assert current_goal.json()["id"] == goal.json()["id"]

    measurement = client.post(
        f"/accounts/{account_id}/users/{user_id}/measurements",
        json={
            "measured_on": date.today().isoformat(),
            "weight_kg": 72.4,
            "neck_cm": 34,
            "waist_cm": 78,
            "hips_cm": 98,
        },
    )
    assert measurement.status_code == 201
    assert measurement.json()["weight_kg"] == 72.4

    users = client.get(f"/accounts/{account_id}/users")
    assert users.status_code == 200
    assert [item["id"] for item in users.json()] == [user_id]

    deleted = client.delete(f"/accounts/{account_id}")
    assert deleted.status_code == 204
    assert client.get(f"/accounts/{account_id}").status_code == 404


def test_measurement_requires_at_least_one_value() -> None:
    account = client.post("/accounts", json={"name": "Validation account"})
    account_id = account.json()["id"]
    user = client.post(
        f"/accounts/{account_id}/users",
        json={"name": "User", "birth_date": None},
    )
    user_id = user.json()["id"]

    response = client.post(
        f"/accounts/{account_id}/users/{user_id}/measurements",
        json={"measured_on": date.today().isoformat()},
    )
    assert response.status_code == 422

    assert client.delete(f"/accounts/{account_id}").status_code == 204


def test_goal_history_timeline() -> None:
    account_id = client.post(
        "/accounts", json={"name": "Goal history account"}
    ).json()["id"]
    user_id = client.post(
        f"/accounts/{account_id}/users",
        json={"name": "User", "birth_date": None, "height_cm": 180},
    ).json()["id"]

    for effective_from, calories in (("2026-01-01", 1800), ("2026-03-01", 2300)):
        response = client.post(
            f"/accounts/{account_id}/users/{user_id}/goals",
            json={
                "daily_calories_kcal": calories,
                "daily_protein_g": 120,
                "daily_fiber_g": 30,
                "effective_from": effective_from,
            },
        )
        assert response.status_code == 201

    timeline = client.get(
        f"/accounts/{account_id}/users/{user_id}/goals/timeline"
        "?date_from=2026-02-01&date_to=2026-04-01"
    )
    assert timeline.status_code == 200
    periods = timeline.json()["periods"]
    assert len(periods) == 2
    assert periods[0]["daily_calories_kcal"] == 1800
    assert periods[0]["period_start"] == "2026-02-01"
    assert periods[0]["period_end"] == "2026-02-28"
    assert periods[1]["daily_calories_kcal"] == 2300
    assert periods[1]["period_start"] == "2026-03-01"
    assert periods[1]["period_end"] == "2026-04-01"

    invalid_height = client.put(
        f"/accounts/{account_id}/users/{user_id}",
        json={"name": "User", "birth_date": None, "height_cm": 350},
    )
    assert invalid_height.status_code == 422

    assert client.delete(f"/accounts/{account_id}").status_code == 204
