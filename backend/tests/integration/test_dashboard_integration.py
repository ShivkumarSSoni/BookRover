"""Integration tests for the Dashboard endpoint.

Tests the full HTTP → Service → Repository → DynamoDB round trip
using moto to mock AWS. Real repositories and a real DashboardService
are wired together; only DynamoDB is replaced by moto's in-memory store.
"""

from decimal import Decimal

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository
from bookrover.repositories.sale_repository import DynamoDBSaleRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.routers.auth import get_current_user
from bookrover.routers.dashboard import get_dashboard_service
from bookrover.services.dashboard_service import DashboardService
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso


def _mock_gl_user(request: Request) -> MeResponse:
    """Inject a group leader identity whose group_leader_id mirrors the URL path parameter."""
    gl_id = request.path_params.get("group_leader_id", "")
    return MeResponse(email="ravi@gmail.com", roles=["group_leader"], group_leader_id=gl_id)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def group_leaders_table(dynamodb_tables):
    """Return the moto-backed group-leaders table."""
    return dynamodb_tables.Table("bookrover-group-leaders-test")


@pytest.fixture
def bookstores_table(dynamodb_tables):
    """Return the moto-backed bookstores table."""
    return dynamodb_tables.Table("bookrover-bookstores-test")


@pytest.fixture
def sellers_table(dynamodb_tables):
    """Return the moto-backed sellers table."""
    return dynamodb_tables.Table("bookrover-sellers-test")


@pytest.fixture
def sales_table(dynamodb_tables):
    """Return the moto-backed sales table."""
    return dynamodb_tables.Table("bookrover-sales-test")


@pytest.fixture
def integration_client(group_leaders_table, bookstores_table, sellers_table, sales_table):
    """TestClient wired with real service + real repositories against moto DynamoDB."""
    real_service = DashboardService(
        group_leader_repository=DynamoDBGroupLeaderRepository(
            table=group_leaders_table,
            sellers_table=sellers_table,
        ),
        bookstore_repository=DynamoDBBookstoreRepository(table=bookstores_table),
        seller_repository=DynamoDBSellerRepository(table=sellers_table),
        sale_repository=DynamoDBSaleRepository(table=sales_table),
    )
    app = create_app()
    app.dependency_overrides[get_dashboard_service] = lambda: real_service
    app.dependency_overrides[get_current_user] = _mock_gl_user
    return TestClient(app)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _seed_bookstore(bookstores_table) -> dict:
    """Insert a bookstore into moto table and return its record."""
    bookstore_id = generate_id()
    now = utc_now_iso()
    item = {
        "bookstore_id": bookstore_id,
        "store_name": "Sri Lakshmi Books",
        "owner_name": "Lakshmi Devi",
        "address": "12 MG Road",
        "phone_number": "+919876543210",
        "created_at": now,
        "updated_at": now,
    }
    bookstores_table.put_item(Item=item)
    return item


def _seed_group_leader(group_leaders_table, bookstore_id: str) -> dict:
    """Insert a group leader into moto table and return their record."""
    group_leader_id = generate_id()
    now = utc_now_iso()
    item = {
        "group_leader_id": group_leader_id,
        "name": "Ravi Kumar",
        "email": "ravi@gmail.com",
        "bookstore_ids": [bookstore_id],
        "created_at": now,
        "updated_at": now,
    }
    group_leaders_table.put_item(Item=item)
    return item


def _seed_seller(sellers_table, group_leader_id: str, bookstore_id: str) -> dict:
    """Insert a seller into moto table and return their record."""
    seller_id = generate_id()
    now = utc_now_iso()
    item = {
        "seller_id": seller_id,
        "first_name": "Anand",
        "last_name": "Raj",
        "email": f"seller-{seller_id}@gmail.com",
        "group_leader_id": group_leader_id,
        "bookstore_id": bookstore_id,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    sellers_table.put_item(Item=item)
    return item


def _seed_sale(sales_table, seller_id: str, total_books: int, total_amount: float) -> dict:
    """Insert a sale record into moto table and return its record."""
    sale_id = generate_id()
    now = utc_now_iso()
    item = {
        "sale_id": sale_id,
        "seller_id": seller_id,
        "bookstore_id": generate_id(),
        "buyer_first_name": "Buyer",
        "buyer_last_name": "Name",
        "buyer_country_code": "+91",
        "buyer_phone": "9876543210",
        "sale_items": [],
        "total_books_sold": total_books,
        "total_amount_collected": Decimal(str(total_amount)),
        "sale_date": now,
        "created_at": now,
    }
    sales_table.put_item(Item=item)
    return item


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_dashboard_returns_200_with_sellers_and_totals(
    integration_client, group_leaders_table, bookstores_table, sellers_table, sales_table
):
    """GET /group-leaders/{id}/dashboard returns 200 with aggregated seller data."""
    bookstore = _seed_bookstore(bookstores_table)
    gl = _seed_group_leader(group_leaders_table, bookstore["bookstore_id"])
    seller = _seed_seller(sellers_table, gl["group_leader_id"], bookstore["bookstore_id"])
    _seed_sale(sales_table, seller["seller_id"], 10, 750.0)
    _seed_sale(sales_table, seller["seller_id"], 15, 1125.0)

    response = integration_client.get(
        f"/group-leaders/{gl['group_leader_id']}/dashboard?bookstore_id={bookstore['bookstore_id']}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["group_leader"]["name"] == "Ravi Kumar"
    assert data["bookstore"]["store_name"] == "Sri Lakshmi Books"
    assert len(data["sellers"]) == 1
    assert data["sellers"][0]["full_name"] == "Anand Raj"
    assert data["sellers"][0]["total_books_sold"] == 25
    assert data["sellers"][0]["total_amount_collected"] == 1875.0
    assert data["totals"]["total_books_sold"] == 25
    assert data["totals"]["total_amount_collected"] == 1875.0


def test_get_dashboard_sorts_by_total_amount_collected_desc_by_default(
    integration_client, group_leaders_table, bookstores_table, sellers_table, sales_table
):
    """GET /group-leaders/{id}/dashboard sorts by total_amount_collected desc by default."""
    bookstore = _seed_bookstore(bookstores_table)
    gl = _seed_group_leader(group_leaders_table, bookstore["bookstore_id"])
    seller1 = _seed_seller(sellers_table, gl["group_leader_id"], bookstore["bookstore_id"])
    seller2 = _seed_seller(sellers_table, gl["group_leader_id"], bookstore["bookstore_id"])
    _seed_sale(sales_table, seller1["seller_id"], 5, 375.0)
    _seed_sale(sales_table, seller2["seller_id"], 25, 1875.0)

    response = integration_client.get(
        f"/group-leaders/{gl['group_leader_id']}/dashboard?bookstore_id={bookstore['bookstore_id']}"
    )

    data = response.json()
    sellers = data["sellers"]
    assert sellers[0]["total_amount_collected"] >= sellers[1]["total_amount_collected"]


def test_get_dashboard_sort_asc(
    integration_client, group_leaders_table, bookstores_table, sellers_table, sales_table
):
    """GET /group-leaders/{id}/dashboard sorts ascending when requested."""
    bookstore = _seed_bookstore(bookstores_table)
    gl = _seed_group_leader(group_leaders_table, bookstore["bookstore_id"])
    seller1 = _seed_seller(sellers_table, gl["group_leader_id"], bookstore["bookstore_id"])
    seller2 = _seed_seller(sellers_table, gl["group_leader_id"], bookstore["bookstore_id"])
    _seed_sale(sales_table, seller1["seller_id"], 5, 375.0)
    _seed_sale(sales_table, seller2["seller_id"], 25, 1875.0)

    response = integration_client.get(
        f"/group-leaders/{gl['group_leader_id']}/dashboard"
        f"?bookstore_id={bookstore['bookstore_id']}&sort_order=asc"
    )

    data = response.json()
    sellers = data["sellers"]
    assert sellers[0]["total_amount_collected"] <= sellers[1]["total_amount_collected"]


def test_get_dashboard_excludes_sellers_from_other_bookstores(
    integration_client, group_leaders_table, bookstores_table, sellers_table, sales_table
):
    """GET /group-leaders/{id}/dashboard excludes sellers from other bookstores."""
    bookstore1 = _seed_bookstore(bookstores_table)
    bookstore2 = _seed_bookstore(bookstores_table)
    # GL linked to both bookstores
    gl_id = generate_id()
    now = utc_now_iso()
    group_leaders_table.put_item(Item={
        "group_leader_id": gl_id,
        "name": "Multi GL",
        "email": "multi@gmail.com",
        "bookstore_ids": [bookstore1["bookstore_id"], bookstore2["bookstore_id"]],
        "created_at": now,
        "updated_at": now,
    })
    seller_bs1 = _seed_seller(sellers_table, gl_id, bookstore1["bookstore_id"])
    seller_bs2 = _seed_seller(sellers_table, gl_id, bookstore2["bookstore_id"])
    _seed_sale(sales_table, seller_bs1["seller_id"], 10, 750.0)
    _seed_sale(sales_table, seller_bs2["seller_id"], 5, 375.0)

    response = integration_client.get(
        f"/group-leaders/{gl_id}/dashboard?bookstore_id={bookstore1['bookstore_id']}"
    )

    data = response.json()
    assert len(data["sellers"]) == 1
    assert data["sellers"][0]["seller_id"] == seller_bs1["seller_id"]


def test_get_dashboard_returns_empty_sellers_list_when_no_sellers(
    integration_client, group_leaders_table, bookstores_table
):
    """GET /group-leaders/{id}/dashboard returns empty sellers when none registered."""
    bookstore = _seed_bookstore(bookstores_table)
    gl = _seed_group_leader(group_leaders_table, bookstore["bookstore_id"])

    response = integration_client.get(
        f"/group-leaders/{gl['group_leader_id']}/dashboard?bookstore_id={bookstore['bookstore_id']}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sellers"] == []
    assert data["totals"]["total_books_sold"] == 0


def test_get_dashboard_returns_404_for_unknown_group_leader(integration_client):
    """GET /group-leaders/{id}/dashboard returns 404 if group leader does not exist."""
    response = integration_client.get(
        "/group-leaders/nonexistent-gl/dashboard?bookstore_id=some-bs"
    )

    assert response.status_code == 404


def test_get_dashboard_returns_404_when_bookstore_not_linked(
    integration_client, group_leaders_table, bookstores_table
):
    """GET /group-leaders/{id}/dashboard returns 404 when bookstore not in GL's list."""
    bookstore = _seed_bookstore(bookstores_table)
    gl = _seed_group_leader(group_leaders_table, bookstore["bookstore_id"])
    other_bookstore = _seed_bookstore(bookstores_table)

    response = integration_client.get(
        f"/group-leaders/{gl['group_leader_id']}/dashboard?bookstore_id={other_bookstore['bookstore_id']}"
    )

    assert response.status_code == 404
