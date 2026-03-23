"""Integration tests for Inventory endpoints.

Tests the full HTTP → Service → Repository → DynamoDB round trip
using moto to mock AWS. Real repositories and a real InventoryService
are wired together; only DynamoDB is replaced by moto's in-memory store.
"""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.repositories.inventory_repository import DynamoDBInventoryRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.routers.auth import get_current_user
from bookrover.routers.inventory import get_inventory_service
from bookrover.services.inventory_service import InventoryService
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso


def _mock_seller_user(request: Request) -> MeResponse:
    """Inject a seller identity whose seller_id mirrors the URL path parameter."""
    seller_id = request.path_params.get("seller_id", "")
    return MeResponse(email="priya@gmail.com", roles=["seller"], seller_id=seller_id)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sellers_table(dynamodb_tables):
    """Return the moto-backed sellers table."""
    return dynamodb_tables.Table("bookrover-sellers-test")


@pytest.fixture
def inventory_table(dynamodb_tables):
    """Return the moto-backed inventory table."""
    return dynamodb_tables.Table("bookrover-inventory-test")


@pytest.fixture
def integration_client(sellers_table, inventory_table):
    """TestClient wired with real service + real repositories against moto DynamoDB."""
    seller_repo = DynamoDBSellerRepository(table=sellers_table)
    inventory_repo = DynamoDBInventoryRepository(table=inventory_table)

    real_service = InventoryService(
        inventory_repository=inventory_repo,
        seller_repository=seller_repo,
    )

    app = create_app()
    app.dependency_overrides[get_inventory_service] = lambda: real_service
    app.dependency_overrides[get_current_user] = _mock_seller_user
    return TestClient(app)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _seed_seller(sellers_table) -> str:
    """Insert a seller into moto table and return their seller_id."""
    seller_id = generate_id()
    now = utc_now_iso()
    sellers_table.put_item(Item={
        "seller_id": seller_id,
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya@gmail.com",
        "group_leader_id": generate_id(),
        "bookstore_id": generate_id(),
        "status": "active",
        "created_at": now,
        "updated_at": now,
    })
    return seller_id


ADD_BOOK_PAYLOAD = {
    "book_name": "Thirukkural",
    "language": "Tamil",
    "initial_count": 10,
    "cost_per_book": 50.00,
    "selling_price": 75.00,
}


# ---------------------------------------------------------------------------
# POST /sellers/{seller_id}/inventory
# ---------------------------------------------------------------------------


def test_add_book_creates_and_returns_full_response(integration_client, sellers_table):
    """Adding a book should persist all fields and return 201 with computed balances."""
    seller_id = _seed_seller(sellers_table)

    response = integration_client.post(f"/sellers/{seller_id}/inventory", json=ADD_BOOK_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["book_name"] == "Thirukkural"
    assert data["language"] == "Tamil"
    assert data["initial_count"] == 10
    assert data["current_count"] == 10  # current == initial on creation
    assert data["cost_per_book"] == 50.00
    assert data["selling_price"] == 75.00
    assert data["current_books_cost_balance"] == 500.00
    assert data["total_books_cost_balance"] == 500.00
    assert data["seller_id"] == seller_id
    assert "book_id" in data
    assert "bookstore_id" in data


def test_add_book_returns_404_for_unknown_seller(integration_client):
    """Adding a book with an unknown seller_id should return 404."""
    response = integration_client.post("/sellers/unknown-seller/inventory", json=ADD_BOOK_PAYLOAD)

    assert response.status_code == 404


def test_add_book_rejects_selling_price_below_cost(integration_client, sellers_table):
    """Adding a book where selling_price <= cost_per_book should return 422."""
    seller_id = _seed_seller(sellers_table)
    payload = {**ADD_BOOK_PAYLOAD, "selling_price": 40.00}

    response = integration_client.post(f"/sellers/{seller_id}/inventory", json=payload)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}/inventory
# ---------------------------------------------------------------------------


def test_get_inventory_returns_added_books(integration_client, sellers_table):
    """Books added via POST should appear in GET /inventory."""
    seller_id = _seed_seller(sellers_table)
    integration_client.post(f"/sellers/{seller_id}/inventory", json=ADD_BOOK_PAYLOAD)

    response = integration_client.get(f"/sellers/{seller_id}/inventory")

    assert response.status_code == 200
    data = response.json()
    assert data["seller_id"] == seller_id
    assert len(data["books"]) == 1
    assert data["books"][0]["book_name"] == "Thirukkural"
    assert data["summary"]["total_books_in_hand"] == 10
    assert data["summary"]["total_cost_balance"] == 500.00


def test_get_inventory_empty_state(integration_client, sellers_table):
    """A seller with no books should return empty books list and zero summary."""
    seller_id = _seed_seller(sellers_table)

    response = integration_client.get(f"/sellers/{seller_id}/inventory")

    assert response.status_code == 200
    data = response.json()
    assert data["books"] == []
    assert data["summary"]["total_books_in_hand"] == 0


def test_get_inventory_returns_404_for_unknown_seller(integration_client):
    """GET /inventory for unknown seller should return 404."""
    response = integration_client.get("/sellers/unknown-seller/inventory")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /sellers/{seller_id}/inventory/{book_id}
# ---------------------------------------------------------------------------


def test_update_book_persists_changed_fields(integration_client, sellers_table):
    """An update should persist only the changed field."""
    seller_id = _seed_seller(sellers_table)
    create_resp = integration_client.post(
        f"/sellers/{seller_id}/inventory", json=ADD_BOOK_PAYLOAD
    )
    book_id = create_resp.json()["book_id"]

    response = integration_client.put(
        f"/sellers/{seller_id}/inventory/{book_id}",
        json={"selling_price": 90.00},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["selling_price"] == 90.00
    assert data["book_name"] == "Thirukkural"  # unchanged


def test_update_book_returns_recomputed_balance(integration_client, sellers_table):
    """Updating cost_per_book should return recomputed balance fields."""
    seller_id = _seed_seller(sellers_table)
    create_resp = integration_client.post(
        f"/sellers/{seller_id}/inventory", json=ADD_BOOK_PAYLOAD
    )
    book_id = create_resp.json()["book_id"]

    response = integration_client.put(
        f"/sellers/{seller_id}/inventory/{book_id}",
        json={"cost_per_book": 60.00, "selling_price": 90.00},
    )

    data = response.json()
    assert data["cost_per_book"] == 60.00
    assert data["current_books_cost_balance"] == 600.00  # 10 × 60


def test_update_book_returns_404_for_unknown_book(integration_client, sellers_table):
    """PUT /inventory/{book_id} for unknown book should return 404."""
    seller_id = _seed_seller(sellers_table)

    response = integration_client.put(
        f"/sellers/{seller_id}/inventory/unknown-book",
        json={"selling_price": 90.00},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /sellers/{seller_id}/inventory/{book_id}
# ---------------------------------------------------------------------------


def test_remove_book_returns_204_when_unsold(integration_client, sellers_table):
    """Deleting an unsold book (current == initial) should return 204."""
    seller_id = _seed_seller(sellers_table)
    create_resp = integration_client.post(
        f"/sellers/{seller_id}/inventory", json=ADD_BOOK_PAYLOAD
    )
    book_id = create_resp.json()["book_id"]

    response = integration_client.delete(f"/sellers/{seller_id}/inventory/{book_id}")

    assert response.status_code == 204


def test_remove_book_no_longer_in_inventory(integration_client, sellers_table):
    """After deletion, the book should not appear in GET /inventory."""
    seller_id = _seed_seller(sellers_table)
    create_resp = integration_client.post(
        f"/sellers/{seller_id}/inventory", json=ADD_BOOK_PAYLOAD
    )
    book_id = create_resp.json()["book_id"]
    integration_client.delete(f"/sellers/{seller_id}/inventory/{book_id}")

    inventory = integration_client.get(f"/sellers/{seller_id}/inventory").json()
    assert inventory["books"] == []


def test_remove_book_returns_404_for_unknown_book(integration_client, sellers_table):
    """DELETE /inventory/{book_id} for unknown book should return 404."""
    seller_id = _seed_seller(sellers_table)

    response = integration_client.delete(f"/sellers/{seller_id}/inventory/unknown-book")

    assert response.status_code == 404
