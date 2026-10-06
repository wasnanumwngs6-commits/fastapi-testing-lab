import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def token(client):
    credentials = {"username": "admin", "password": "admin123"}
    response = client.post("/api/auth/login", json=credentials)
    return response.json()["token"]


@pytest.fixture
def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_returns_200(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    invalid_id = client.get("/api/products/abc")
    assert invalid_id.status_code == 400
    assert invalid_id.json() == {"error": "id must be a positive integer"}

    missing_route = client.get("/route-that-does-not-exist")
    assert missing_route.status_code == 404
    assert missing_route.json() == {"error": "Route not found"}


def test_login_wrong_password_returns_401(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )

    assert response.status_code == 401


def test_create_product_without_token_returns_401(client):
    response = client.post(
        "/api/products",
        json={"name": "Monitor", "price": 5990, "stock": 3},
    )

    assert response.status_code == 401


def test_create_product_invalid_data_returns_400(client, auth):
    response = client.post(
        "/api/products",
        headers=auth,
        json={"name": "", "price": -10, "stock": 1},
    )

    assert response.status_code == 400
    assert "name is required" in response.json()["details"]
    assert "price must be a number greater than 0" in response.json()["details"]

    malformed_json = client.post(
        "/api/products",
        headers={**auth, "Content-Type": "application/json"},
        content='{"price": }',
    )
    assert malformed_json.status_code == 400
    assert malformed_json.json() == {"error": "Invalid JSON body"}


def test_crud_flow(client, auth):
    created = client.post(
        "/api/products",
        headers=auth,
        json={"name": "Monitor", "price": 5990, "stock": 3, "discountPercent": 15},
    )
    assert created.status_code == 201
    assert created.json()["finalPrice"] == 5091.5
    product_id = created.json()["id"]

    fetched = client.get(f"/api/products/{product_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Monitor"

    updated = client.put(
        f"/api/products/{product_id}",
        headers=auth,
        json={"stock": 10, "discountPercent": 0},
    )
    assert updated.status_code == 200
    assert updated.json()["stock"] == 10
    assert updated.json()["finalPrice"] == 5990

    deleted = client.delete(f"/api/products/{product_id}", headers=auth)
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert client.get(f"/api/products/{product_id}").status_code == 404
    assert client.delete(
        f"/api/products/{product_id}", headers=auth
    ).status_code == 404
