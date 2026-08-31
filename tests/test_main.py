from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI backend is running"}


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_products_crud() -> None:
    payload = {
        "name": "Гречка варёная",
        "brand": None,
        "category": "Крупы",
        "barcode": None,
        "description": "Без масла",
        "calories_kcal": 110,
        "protein_g": 4.2,
        "fat_g": 1.1,
        "carbohydrates_g": 21.3,
        "fiber_g": 2.7,
    }

    created = client.post("/products", json=payload)
    assert created.status_code == 201
    product_id = created.json()["id"]

    fetched = client.get(f"/products/{product_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == payload["name"]
    assert fetched.json()["protein_g"] == payload["protein_g"]

    updated_payload = {**payload, "name": "Гречка"}
    updated = client.put(f"/products/{product_id}", json=updated_payload)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Гречка"

    listed = client.get("/products?limit=500")
    assert listed.status_code == 200
    assert any(product["id"] == product_id for product in listed.json())

    deleted = client.delete(f"/products/{product_id}")
    assert deleted.status_code == 204
    assert client.get(f"/products/{product_id}").status_code == 404


def test_product_rejects_negative_nutrition() -> None:
    response = client.post(
        "/products",
        json={
            "name": "Некорректный продукт",
            "calories_kcal": -1,
            "protein_g": 0,
            "fat_g": 0,
            "carbohydrates_g": 0,
            "fiber_g": 0,
        },
    )

    assert response.status_code == 422
