"""Проверки публичного контракта учебного API."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_redirects_to_swagger_ui() -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_collection_returns_five_devices_and_metadata() -> None:
    response = client.get("/api/products")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 5
    assert len(body["data"]) == 5
    assert [p["id"] for p in body["data"]] == [1, 2, 3, 4, 5]


def test_one_device_has_expected_json_representation() -> None:
    response = client.get("/api/products/5")
    assert response.status_code == 200
    assert response.json() == {
        "id": 5,
        "name": "Relay Controller",
        "type": "controller",
        "status": "active",
        "price": 59.9,
        "tags": ["power"],
    }


def test_unknown_device_returns_404() -> None:
    response = client.get("/api/products/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Устройство 999 не найдено"}


def test_non_positive_or_invalid_id_returns_validation_error() -> None:
    for path in ["/api/products/0", "/api/products/abc"]:
        assert client.get(path).status_code == 422


def test_openapi_and_docs_are_available() -> None:
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    paths = schema.json()["paths"]
    assert "/api/products" in paths
    assert "get" in paths["/api/products"]
    assert "/api/products/{product_id}" in paths
    assert client.get("/docs").status_code == 200


def test_no_mutation_methods_are_defined() -> None:
    assert client.post("/api/products", json={"name": "X"}).status_code == 405
    assert client.delete("/api/products/5").status_code == 405
