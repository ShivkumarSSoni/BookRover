"""Unit tests for the Inventory router.

Verifies HTTP behaviour using FastAPI TestClient with a mocked
AbstractInventoryService injected via Depends(). No repository, no DynamoDB,
no moto required.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.exceptions.conflict import BookPartiallySoldError
from bookrover.exceptions.not_found import BookNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_inventory_service import AbstractInventoryService
from bookrover.main import create_app
from bookrover.models.inventory import BookResponse, InventoryListResponse, InventorySummary
from bookrover.routers.inventory import get_inventory_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    """Mock AbstractInventoryService."""
    return MagicMock(spec=AbstractInventoryService)


@pytest.fixture
def client(mock_service):
    """TestClient with the mock service injected via dependency override."""
    app = create_app()
    app.dependency_overrides[get_inventory_service] = lambda: mock_service
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOOK_RESPONSE = BookResponse(
    book_id="book-001",
    seller_id="sel-001",
    bookstore_id="bs-001",
    book_name="Thirukkural",
    language="Tamil",
    initial_count=10,
    current_count=10,
    cost_per_book=50.00,
    selling_price=75.00,
    current_books_cost_balance=500.00,
    total_books_cost_balance=500.00,
    created_at="2026-01-01T00:00:00Z",
    updated_at="2026-01-01T00:00:00Z",
)

INVENTORY_RESPONSE = InventoryListResponse(
    seller_id="sel-001",
    bookstore_id="bs-001",
    books=[BOOK_RESPONSE],
    summary=InventorySummary(
        total_books_in_hand=10,
        total_cost_balance=500.00,
        total_initial_cost=500.00,
    ),
)

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


def test_add_book_returns_201(client, mock_service):
    """POST /sellers/{id}/inventory should return 201 with the created book."""
    mock_service.add_book.return_value = BOOK_RESPONSE

    response = client.post("/sellers/sel-001/inventory", json=ADD_BOOK_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["book_id"] == "book-001"
    assert data["book_name"] == "Thirukkural"
    assert data["current_books_cost_balance"] == 500.00


def test_add_book_returns_404_for_unknown_seller(client, mock_service):
    """POST /sellers/{id}/inventory should return 404 if seller not found."""
    mock_service.add_book.side_effect = SellerNotFoundError("unknown-seller")

    response = client.post("/sellers/unknown-seller/inventory", json=ADD_BOOK_PAYLOAD)

    assert response.status_code == 404
    assert "unknown-seller" in response.json()["detail"]


def test_add_book_validates_selling_price_below_cost(client, mock_service):
    """POST /sellers/{id}/inventory should return 422 if selling_price <= cost_per_book."""
    payload = {**ADD_BOOK_PAYLOAD, "selling_price": 40.00}  # below cost

    response = client.post("/sellers/sel-001/inventory", json=payload)

    assert response.status_code == 422


def test_add_book_validates_missing_fields(client, mock_service):
    """POST /sellers/{id}/inventory should return 422 for missing required fields."""
    response = client.post("/sellers/sel-001/inventory", json={"book_name": "Only Name"})

    assert response.status_code == 422


def test_add_book_validates_initial_count_min(client, mock_service):
    """POST /sellers/{id}/inventory should return 422 if initial_count < 1."""
    payload = {**ADD_BOOK_PAYLOAD, "initial_count": 0}

    response = client.post("/sellers/sel-001/inventory", json=payload)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}/inventory
# ---------------------------------------------------------------------------


def test_get_inventory_returns_200(client, mock_service):
    """GET /sellers/{id}/inventory should return 200 with inventory data."""
    mock_service.get_inventory.return_value = INVENTORY_RESPONSE

    response = client.get("/sellers/sel-001/inventory")

    assert response.status_code == 200
    data = response.json()
    assert data["seller_id"] == "sel-001"
    assert len(data["books"]) == 1
    assert data["summary"]["total_books_in_hand"] == 10


def test_get_inventory_returns_404_for_unknown_seller(client, mock_service):
    """GET /sellers/{id}/inventory should return 404 if seller not found."""
    mock_service.get_inventory.side_effect = SellerNotFoundError("unknown")

    response = client.get("/sellers/unknown/inventory")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /sellers/{seller_id}/inventory/{book_id}
# ---------------------------------------------------------------------------


def test_update_book_returns_200(client, mock_service):
    """PUT /sellers/{id}/inventory/{book_id} should return 200 with updated book."""
    updated = BookResponse(**{**BOOK_RESPONSE.model_dump(), "selling_price": 80.00,
                               "current_books_cost_balance": 500.00,
                               "total_books_cost_balance": 500.00})
    mock_service.update_book.return_value = updated

    response = client.put(
        "/sellers/sel-001/inventory/book-001",
        json={"selling_price": 80.00},
    )

    assert response.status_code == 200
    assert response.json()["selling_price"] == 80.00


def test_update_book_returns_404_when_not_found(client, mock_service):
    """PUT /sellers/{id}/inventory/{book_id} should return 404 if book not found."""
    mock_service.update_book.side_effect = BookNotFoundError("book-001")

    response = client.put(
        "/sellers/sel-001/inventory/book-001",
        json={"selling_price": 80.00},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /sellers/{seller_id}/inventory/{book_id}
# ---------------------------------------------------------------------------


def test_remove_book_returns_204(client, mock_service):
    """DELETE /sellers/{id}/inventory/{book_id} should return 204 on success."""
    mock_service.remove_book.return_value = None

    response = client.delete("/sellers/sel-001/inventory/book-001")

    assert response.status_code == 204


def test_remove_book_returns_404_when_not_found(client, mock_service):
    """DELETE /sellers/{id}/inventory/{book_id} should return 404 if book not found."""
    mock_service.remove_book.side_effect = BookNotFoundError("book-001")

    response = client.delete("/sellers/sel-001/inventory/book-001")

    assert response.status_code == 404


def test_remove_book_returns_409_when_partially_sold(client, mock_service):
    """DELETE /sellers/{id}/inventory/{book_id} should return 409 if partially sold."""
    mock_service.remove_book.side_effect = BookPartiallySoldError("book-001")

    response = client.delete("/sellers/sel-001/inventory/book-001")

    assert response.status_code == 409
    assert "partially sold" in response.json()["detail"]
