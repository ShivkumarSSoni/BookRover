"""Integration tests for Returns endpoints.

Tests the full HTTP → Service → Repository → DynamoDB round trip
using moto to mock AWS. Real repositories and a real ReturnService
are wired together; only DynamoDB is replaced by moto's in-memory store.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from bookrover.main import create_app
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.inventory_repository import DynamoDBInventoryRepository
from bookrover.repositories.return_repository import DynamoDBReturnRepository
from bookrover.repositories.sale_repository import DynamoDBSaleRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.routers.returns import get_return_service
from bookrover.services.return_service import ReturnService
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sellers_table(dynamodb_tables):
    return dynamodb_tables.Table("bookrover-sellers-test")


@pytest.fixture
def bookstores_table(dynamodb_tables):
    return dynamodb_tables.Table("bookrover-bookstores-test")


@pytest.fixture
def inventory_table(dynamodb_tables):
    return dynamodb_tables.Table("bookrover-inventory-test")


@pytest.fixture
def sales_table(dynamodb_tables):
    return dynamodb_tables.Table("bookrover-sales-test")


@pytest.fixture
def returns_table(dynamodb_tables):
    return dynamodb_tables.Table("bookrover-returns-test")


@pytest.fixture
def integration_client(
    sellers_table, bookstores_table, inventory_table, sales_table, returns_table
):
    """TestClient wired with real service + real repositories against moto DynamoDB."""
    real_service = ReturnService(
        seller_repository=DynamoDBSellerRepository(table=sellers_table),
        bookstore_repository=DynamoDBBookstoreRepository(table=bookstores_table),
        inventory_repository=DynamoDBInventoryRepository(table=inventory_table),
        sale_repository=DynamoDBSaleRepository(table=sales_table),
        return_repository=DynamoDBReturnRepository(table=returns_table),
    )
    app = create_app()
    app.dependency_overrides[get_return_service] = lambda: real_service
    return TestClient(app)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _seed_bookstore(bookstores_table) -> dict:
    item = {
        "bookstore_id": generate_id(),
        "store_name": "Sri Lakshmi Books",
        "owner_name": "Lakshmi Devi",
        "address": "12 MG Road, Chennai",
        "phone_number": "+914423456789",
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    bookstores_table.put_item(Item=item)
    return item


def _seed_seller(sellers_table, bookstore_id: str, status: str = "active") -> dict:
    item = {
        "seller_id": generate_id(),
        "first_name": "Anand",
        "last_name": "Raj",
        "email": "anand@gmail.com",
        "group_leader_id": generate_id(),
        "bookstore_id": bookstore_id,
        "status": status,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    sellers_table.put_item(Item=item)
    return item


def _seed_book(inventory_table, seller_id: str, bookstore_id: str, current_count: int = 8) -> dict:
    item = {
        "book_id": generate_id(),
        "seller_id": seller_id,
        "bookstore_id": bookstore_id,
        "book_name": "Thirukkural",
        "language": "Tamil",
        "initial_count": Decimal(str(current_count)),
        "current_count": Decimal(str(current_count)),
        "cost_per_book": Decimal("50.00"),
        "selling_price": Decimal("75.00"),
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    inventory_table.put_item(Item=item)
    return item


def _seed_sale(sales_table, seller_id: str, bookstore_id: str, amount: str = "225.00") -> dict:
    item = {
        "sale_id": generate_id(),
        "seller_id": seller_id,
        "bookstore_id": bookstore_id,
        "buyer_first_name": "Ravi",
        "buyer_last_name": "Kumar",
        "buyer_country_code": "+91",
        "buyer_phone": "9876543210",
        "sale_items": [],
        "total_books_sold": Decimal("3"),
        "total_amount_collected": Decimal(amount),
        "sale_date": utc_now_iso(),
        "created_at": utc_now_iso(),
    }
    sales_table.put_item(Item=item)
    return item


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}/return-summary
# ---------------------------------------------------------------------------


def test_get_return_summary_returns_200_with_bookstore_and_books(
    integration_client, sellers_table, bookstores_table, inventory_table, sales_table
):
    """GET /sellers/{id}/return-summary returns 200 with bookstore info and books."""
    bookstore = _seed_bookstore(bookstores_table)
    seller = _seed_seller(sellers_table, bookstore["bookstore_id"])
    _seed_book(inventory_table, seller["seller_id"], bookstore["bookstore_id"])

    response = integration_client.get(f"/sellers/{seller['seller_id']}/return-summary")

    assert response.status_code == 200
    data = response.json()
    assert data["seller_id"] == seller["seller_id"]
    assert data["bookstore"]["store_name"] == "Sri Lakshmi Books"
    assert len(data["books_to_return"]) == 1
    assert data["total_books_to_return"] == 8


def test_get_return_summary_aggregates_money_from_sales(
    integration_client, sellers_table, bookstores_table, inventory_table, sales_table
):
    """GET /sellers/{id}/return-summary sums money from all sales."""
    bookstore = _seed_bookstore(bookstores_table)
    seller = _seed_seller(sellers_table, bookstore["bookstore_id"])
    _seed_sale(sales_table, seller["seller_id"], bookstore["bookstore_id"], "100.00")
    _seed_sale(sales_table, seller["seller_id"], bookstore["bookstore_id"], "125.00")

    response = integration_client.get(f"/sellers/{seller['seller_id']}/return-summary")

    assert response.status_code == 200
    assert response.json()["total_money_collected_from_sales"] == pytest.approx(225.0)


def test_get_return_summary_excludes_sold_out_books(
    integration_client, sellers_table, bookstores_table, inventory_table, sales_table
):
    """GET /sellers/{id}/return-summary excludes books with current_count = 0."""
    bookstore = _seed_bookstore(bookstores_table)
    seller = _seed_seller(sellers_table, bookstore["bookstore_id"])
    _seed_book(inventory_table, seller["seller_id"], bookstore["bookstore_id"], current_count=0)
    _seed_book(inventory_table, seller["seller_id"], bookstore["bookstore_id"], current_count=5)

    response = integration_client.get(f"/sellers/{seller['seller_id']}/return-summary")

    assert response.status_code == 200
    assert response.json()["total_books_to_return"] == 5
    assert len(response.json()["books_to_return"]) == 1


def test_get_return_summary_returns_404_for_unknown_seller(integration_client):
    """GET /sellers/{id}/return-summary returns 404 for an unknown seller ID."""
    response = integration_client.get("/sellers/nonexistent-seller/return-summary")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /sellers/{seller_id}/returns
# ---------------------------------------------------------------------------


def test_submit_return_returns_201_and_persists_record(
    integration_client, sellers_table, bookstores_table, inventory_table, returns_table
):
    """POST /sellers/{id}/returns returns 201 and the return is stored in DynamoDB."""
    bookstore = _seed_bookstore(bookstores_table)
    seller = _seed_seller(sellers_table, bookstore["bookstore_id"])
    _seed_book(inventory_table, seller["seller_id"], bookstore["bookstore_id"])

    response = integration_client.post(
        f"/sellers/{seller['seller_id']}/returns", json={}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["seller_id"] == seller["seller_id"]
    assert data["status"] == "completed"
    assert data["total_books_returned"] == 8


def test_submit_return_clears_inventory(
    integration_client, sellers_table, bookstores_table, inventory_table, sales_table, returns_table
):
    """POST /sellers/{id}/returns deletes all inventory books after submission."""
    bookstore = _seed_bookstore(bookstores_table)
    seller = _seed_seller(sellers_table, bookstore["bookstore_id"])
    _seed_book(inventory_table, seller["seller_id"], bookstore["bookstore_id"])
    _seed_book(inventory_table, seller["seller_id"], bookstore["bookstore_id"])

    integration_client.post(f"/sellers/{seller['seller_id']}/returns", json={})

    from boto3.dynamodb.conditions import Key
    remaining = inventory_table.query(
        IndexName="seller-id-index",
        KeyConditionExpression=Key("seller_id").eq(seller["seller_id"]),
    )["Items"]
    assert remaining == []


def test_submit_return_resets_seller_status_to_active(
    integration_client, sellers_table, bookstores_table, inventory_table, returns_table
):
    """POST /sellers/{id}/returns resets seller status to 'active'."""
    bookstore = _seed_bookstore(bookstores_table)
    seller = _seed_seller(sellers_table, bookstore["bookstore_id"], status="pending_return")

    integration_client.post(f"/sellers/{seller['seller_id']}/returns", json={})

    updated = sellers_table.get_item(Key={"seller_id": seller["seller_id"]})["Item"]
    assert updated["status"] == "active"


def test_submit_return_returns_404_for_unknown_seller(integration_client):
    """POST /sellers/{id}/returns returns 404 for an unknown seller ID."""
    response = integration_client.post("/sellers/nonexistent-seller/returns", json={})

    assert response.status_code == 404
