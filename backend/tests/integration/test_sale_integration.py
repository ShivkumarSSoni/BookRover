"""Integration tests for Sales endpoints.

Tests the full HTTP → Service → Repository → DynamoDB round trip
using moto to mock AWS. Real repositories and a real SaleService
are wired together; only DynamoDB is replaced by moto's in-memory store.
"""

from decimal import Decimal

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.repositories.inventory_repository import DynamoDBInventoryRepository
from bookrover.repositories.sale_repository import DynamoDBSaleRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.routers.auth import get_current_user
from bookrover.routers.sales import get_sale_service
from bookrover.services.sale_service import SaleService
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
def sales_table(dynamodb_tables):
    """Return the moto-backed sales table."""
    return dynamodb_tables.Table("bookrover-sales-test")


@pytest.fixture
def integration_client(sellers_table, inventory_table, sales_table):
    """TestClient wired with real service + real repositories against moto DynamoDB."""
    real_service = SaleService(
        sale_repository=DynamoDBSaleRepository(table=sales_table),
        inventory_repository=DynamoDBInventoryRepository(table=inventory_table),
        seller_repository=DynamoDBSellerRepository(table=sellers_table),
    )
    app = create_app()
    app.dependency_overrides[get_sale_service] = lambda: real_service
    app.dependency_overrides[get_current_user] = _mock_seller_user
    return TestClient(app)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _seed_seller(sellers_table, status: str = "active") -> dict:
    """Insert a seller into moto table and return their record."""
    seller_id = generate_id()
    bookstore_id = generate_id()
    now = utc_now_iso()
    item = {
        "seller_id": seller_id,
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya@gmail.com",
        "group_leader_id": generate_id(),
        "bookstore_id": bookstore_id,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    sellers_table.put_item(Item=item)
    return item


def _seed_book(inventory_table, seller_id: str, bookstore_id: str, current_count: int = 10) -> dict:
    """Insert a book into moto inventory table and return its record."""
    book_id = generate_id()
    now = utc_now_iso()
    item = {
        "book_id": book_id,
        "seller_id": seller_id,
        "bookstore_id": bookstore_id,
        "book_name": "Thirukkural",
        "language": "Tamil",
        "initial_count": Decimal(str(current_count)),
        "current_count": Decimal(str(current_count)),
        "cost_per_book": Decimal("50.00"),
        "selling_price": Decimal("75.00"),
        "created_at": now,
        "updated_at": now,
    }
    inventory_table.put_item(Item=item)
    return item


def _sale_payload(book_id: str, quantity: int = 2) -> dict:
    return {
        "buyer_first_name": "Ravi",
        "buyer_last_name": "Kumar",
        "buyer_country_code": "+91",
        "buyer_phone": "9876543210",
        "items": [{"book_id": book_id, "quantity_sold": quantity}],
    }


# ---------------------------------------------------------------------------
# POST /sellers/{seller_id}/sales
# ---------------------------------------------------------------------------


def test_create_sale_returns_201_and_persists_record(
    integration_client, sellers_table, inventory_table, sales_table
):
    """POST /sellers/{id}/sales should return 201 and write sale to DynamoDB."""
    seller = _seed_seller(sellers_table)
    book = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"])

    response = integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload(book["book_id"], quantity=2),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["seller_id"] == seller["seller_id"]
    assert data["total_books_sold"] == 2
    assert data["total_amount_collected"] == 150.0
    assert data["sale_items"][0]["book_name"] == "Thirukkural"

    # Verify persisted in DynamoDB
    persisted = sales_table.get_item(Key={"sale_id": data["sale_id"]}).get("Item")
    assert persisted is not None
    assert persisted["seller_id"] == seller["seller_id"]


def test_create_sale_decrements_inventory_current_count(
    integration_client, sellers_table, inventory_table
):
    """POST /sellers/{id}/sales should decrement current_count by quantity_sold."""
    seller = _seed_seller(sellers_table)
    book = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"], current_count=10)

    integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload(book["book_id"], quantity=3),
    )

    updated = inventory_table.get_item(Key={"book_id": book["book_id"]}).get("Item")
    assert int(updated["current_count"]) == 7  # 10 - 3


def test_create_sale_with_multiple_items(
    integration_client, sellers_table, inventory_table
):
    """POST /sellers/{id}/sales should handle multiple books in one sale."""
    seller = _seed_seller(sellers_table)
    book1 = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"], current_count=5)
    book2 = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"], current_count=8)

    payload = {
        "buyer_first_name": "Ravi",
        "buyer_last_name": "Kumar",
        "buyer_country_code": "+91",
        "buyer_phone": "9876543210",
        "items": [
            {"book_id": book1["book_id"], "quantity_sold": 2},
            {"book_id": book2["book_id"], "quantity_sold": 3},
        ],
    }

    response = integration_client.post(f"/sellers/{seller['seller_id']}/sales", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["total_books_sold"] == 5
    assert len(data["sale_items"]) == 2

    updated1 = inventory_table.get_item(Key={"book_id": book1["book_id"]}).get("Item")
    updated2 = inventory_table.get_item(Key={"book_id": book2["book_id"]}).get("Item")
    assert int(updated1["current_count"]) == 3
    assert int(updated2["current_count"]) == 5


def test_create_sale_returns_404_for_unknown_seller(integration_client):
    """POST /sellers/{id}/sales should return 404 if seller does not exist."""
    payload = _sale_payload("any-book-id")

    response = integration_client.post("/sellers/nonexistent-seller/sales", json=payload)

    assert response.status_code == 404


def test_create_sale_returns_404_for_unknown_book(
    integration_client, sellers_table
):
    """POST /sellers/{id}/sales should return 404 if book_id does not exist."""
    seller = _seed_seller(sellers_table)

    response = integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload("nonexistent-book"),
    )

    assert response.status_code == 404


def test_create_sale_returns_400_for_insufficient_inventory(
    integration_client, sellers_table, inventory_table
):
    """POST /sellers/{id}/sales should return 400 when quantity exceeds current_count."""
    seller = _seed_seller(sellers_table)
    book = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"], current_count=2)

    response = integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload(book["book_id"], quantity=5),
    )

    assert response.status_code == 400
    assert "book" in response.json()["detail"].lower()


def test_create_sale_returns_409_for_pending_return_seller(
    integration_client, sellers_table, inventory_table
):
    """POST /sellers/{id}/sales should return 409 if seller status is pending_return."""
    seller = _seed_seller(sellers_table, status="pending_return")
    book = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"])

    response = integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload(book["book_id"]),
    )

    assert response.status_code == 409


def test_create_sale_does_not_decrement_on_validation_failure(
    integration_client, sellers_table, inventory_table
):
    """POST /sellers/{id}/sales should leave inventory unchanged if validation fails."""
    seller = _seed_seller(sellers_table)
    book = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"], current_count=3)

    # Request more than available
    integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload(book["book_id"], quantity=10),
    )

    unchanged = inventory_table.get_item(Key={"book_id": book["book_id"]}).get("Item")
    assert int(unchanged["current_count"]) == 3


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}/sales
# ---------------------------------------------------------------------------


def test_list_sales_returns_empty_for_new_seller(integration_client, sellers_table):
    """GET /sellers/{id}/sales should return empty list when seller has no sales."""
    seller = _seed_seller(sellers_table)

    response = integration_client.get(f"/sellers/{seller['seller_id']}/sales")

    assert response.status_code == 200
    assert response.json() == []


def test_list_sales_returns_created_sales(
    integration_client, sellers_table, inventory_table
):
    """GET /sellers/{id}/sales should return all sales recorded for the seller."""
    seller = _seed_seller(sellers_table)
    book = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"])

    integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload(book["book_id"], quantity=1),
    )
    integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload(book["book_id"], quantity=1),
    )

    response = integration_client.get(f"/sellers/{seller['seller_id']}/sales")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}/sales/{sale_id}
# ---------------------------------------------------------------------------


def test_get_sale_returns_200_for_valid_ids(
    integration_client, sellers_table, inventory_table
):
    """GET /sellers/{id}/sales/{sale_id} should return the full sale record."""
    seller = _seed_seller(sellers_table)
    book = _seed_book(inventory_table, seller["seller_id"], seller["bookstore_id"])

    create_resp = integration_client.post(
        f"/sellers/{seller['seller_id']}/sales",
        json=_sale_payload(book["book_id"], quantity=2),
    )
    sale_id = create_resp.json()["sale_id"]

    response = integration_client.get(f"/sellers/{seller['seller_id']}/sales/{sale_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["sale_id"] == sale_id
    assert data["total_books_sold"] == 2


def test_get_sale_returns_404_for_missing_sale(integration_client, sellers_table):
    """GET /sellers/{id}/sales/{sale_id} should return 404 if sale does not exist."""
    seller = _seed_seller(sellers_table)

    response = integration_client.get(f"/sellers/{seller['seller_id']}/sales/nonexistent-sale")

    assert response.status_code == 404


def test_get_sale_returns_404_for_wrong_seller(
    integration_client, sellers_table, inventory_table
):
    """GET /sellers/{id}/sales/{sale_id} should return 404 if sale belongs to a different seller."""
    seller1 = _seed_seller(sellers_table)
    seller2 = _seed_seller(sellers_table)
    book = _seed_book(inventory_table, seller1["seller_id"], seller1["bookstore_id"])

    create_resp = integration_client.post(
        f"/sellers/{seller1['seller_id']}/sales",
        json=_sale_payload(book["book_id"]),
    )
    sale_id = create_resp.json()["sale_id"]

    # seller2 tries to access seller1's sale
    response = integration_client.get(f"/sellers/{seller2['seller_id']}/sales/{sale_id}")

    assert response.status_code == 404
