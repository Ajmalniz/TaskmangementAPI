from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_item():
    response = client.post(
        "/api/v1/items",
        json={"name": "Test Item", "price": 10.5, "description": "A test item"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"
    assert response.json()["price"] == 10.5


def test_read_items():
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_item():
    # Create an item first
    create_response = client.post(
        "/api/v1/items",
        json={"name": "Test Item", "price": 10.5}
    )
    item_id = create_response.json()["id"]

    # Read the item
    response = client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_read_nonexistent_item():
    response = client.get("/api/v1/items/999")
    assert response.status_code == 404


def test_update_item():
    # Create an item first
    create_response = client.post(
        "/api/v1/items",
        json={"name": "Test Item", "price": 10.5}
    )
    item_id = create_response.json()["id"]

    # Update the item
    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"name": "Updated Item", "price": 20.0}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Item"
    assert response.json()["price"] == 20.0


def test_delete_item():
    # Create an item first
    create_response = client.post(
        "/api/v1/items",
        json={"name": "Test Item", "price": 10.5}
    )
    item_id = create_response.json()["id"]

    # Delete the item
    response = client.delete(f"/api/v1/items/{item_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/v1/items/{item_id}")
    assert get_response.status_code == 404
