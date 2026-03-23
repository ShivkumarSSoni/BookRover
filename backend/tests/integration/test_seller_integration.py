"""Integration tests for Seller and Lookup endpoints.

Tests the full HTTP → Service → Repository → DynamoDB round trip
using moto to mock AWS. Real repositories and a real SellerService are
wired together; only DynamoDB is replaced by moto's in-memory store.
"""

import pytest
from fastapi.testclient import TestClient

from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository
from bookrover.repositories.seller_repository import DynamoDBSellerRepository
from bookrover.routers.auth import get_current_user
from bookrover.routers.lookup import get_lookup_repos
from bookrover.routers.sellers import get_seller_service
from bookrover.services.seller_service import SellerService
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso

SELLER_ME = MeResponse(email="priya@gmail.com", roles=["seller", "admin"])

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bookstore_table(dynamodb_tables):
    """Return the moto-backed bookstores table."""
    return dynamodb_tables.Table("bookrover-bookstores-test")


@pytest.fixture
def group_leaders_table(dynamodb_tables):
    """Return the moto-backed group leaders table."""
    return dynamodb_tables.Table("bookrover-group-leaders-test")


@pytest.fixture
def sellers_table(dynamodb_tables):
    """Return the moto-backed sellers table."""
    return dynamodb_tables.Table("bookrover-sellers-test")


@pytest.fixture
def integration_client(bookstore_table, group_leaders_table, sellers_table):
    """TestClient wired with real service + real repositories against moto DynamoDB."""
    bookstore_repo = DynamoDBBookstoreRepository(table=bookstore_table)
    group_leader_repo = DynamoDBGroupLeaderRepository(
        table=group_leaders_table,
        sellers_table=sellers_table,
    )
    seller_repo = DynamoDBSellerRepository(table=sellers_table)

    real_service = SellerService(
        seller_repository=seller_repo,
        group_leader_repository=group_leader_repo,
        bookstore_repository=bookstore_repo,
    )

    app = create_app()
    app.dependency_overrides[get_seller_service] = lambda: real_service
    app.dependency_overrides[get_lookup_repos] = lambda: (group_leader_repo, bookstore_repo)
    app.dependency_overrides[get_current_user] = lambda: SELLER_ME
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers — seed data
# ---------------------------------------------------------------------------


def _seed_bookstore(bookstore_table) -> str:
    """Insert a bookstore into the moto table and return its bookstore_id."""
    bookstore_id = generate_id()
    now = utc_now_iso()
    bookstore_table.put_item(Item={
        "bookstore_id": bookstore_id,
        "store_name": "Sri Lakshmi Books",
        "owner_name": "Lakshmi Devi",
        "address": "12 MG Road, Chennai",
        "phone_number": "+914423456789",
        "created_at": now,
        "updated_at": now,
    })
    return bookstore_id


def _seed_group_leader(group_leaders_table, bookstore_ids: list) -> str:
    """Insert a group leader into the moto table and return their group_leader_id."""
    group_leader_id = generate_id()
    now = utc_now_iso()
    group_leaders_table.put_item(Item={
        "group_leader_id": group_leader_id,
        "name": "Ravi Kumar",
        "email": "ravi@gmail.com",
        "bookstore_ids": bookstore_ids,
        "created_at": now,
        "updated_at": now,
    })
    return group_leader_id


# ---------------------------------------------------------------------------
# POST /sellers — integration tests
# ---------------------------------------------------------------------------


def test_register_seller_creates_and_returns_full_response(
    integration_client, bookstore_table, group_leaders_table
):
    """Registering a seller should persist all fields and return 201 with the seller data."""
    bookstore_id = _seed_bookstore(bookstore_table)
    group_leader_id = _seed_group_leader(group_leaders_table, [bookstore_id])

    payload = {
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya@gmail.com",
        "group_leader_id": group_leader_id,
        "bookstore_id": bookstore_id,
    }

    response = integration_client.post("/sellers", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Priya"
    assert data["last_name"] == "Sharma"
    assert data["email"] == "priya@gmail.com"
    assert data["group_leader_id"] == group_leader_id
    assert data["bookstore_id"] == bookstore_id
    assert data["status"] == "active"
    assert "seller_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_register_seller_returns_409_for_duplicate_email(
    integration_client, bookstore_table, group_leaders_table
):
    """Registering with an email that already exists should return 409."""
    bookstore_id = _seed_bookstore(bookstore_table)
    group_leader_id = _seed_group_leader(group_leaders_table, [bookstore_id])

    payload = {
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya@gmail.com",
        "group_leader_id": group_leader_id,
        "bookstore_id": bookstore_id,
    }

    integration_client.post("/sellers", json=payload)
    response = integration_client.post("/sellers", json=payload)

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_register_seller_returns_404_for_missing_group_leader(
    integration_client, bookstore_table
):
    """Registering with an unknown group_leader_id should return 404."""
    bookstore_id = _seed_bookstore(bookstore_table)

    payload = {
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya@gmail.com",
        "group_leader_id": "nonexistent-gl",
        "bookstore_id": bookstore_id,
    }

    response = integration_client.post("/sellers", json=payload)

    assert response.status_code == 404
    assert "nonexistent-gl" in response.json()["detail"]


def test_register_seller_returns_404_for_missing_bookstore(
    integration_client, group_leaders_table
):
    """Registering with an unknown bookstore_id should return 404."""
    group_leader_id = _seed_group_leader(group_leaders_table, [])

    payload = {
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya@gmail.com",
        "group_leader_id": group_leader_id,
        "bookstore_id": "nonexistent-bs",
    }

    response = integration_client.post("/sellers", json=payload)

    assert response.status_code == 404
    assert "nonexistent-bs" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id} — integration tests
# ---------------------------------------------------------------------------


def test_get_seller_returns_registered_seller(
    integration_client, bookstore_table, group_leaders_table
):
    """Fetching a seller by ID after registration should return the same data."""
    bookstore_id = _seed_bookstore(bookstore_table)
    group_leader_id = _seed_group_leader(group_leaders_table, [bookstore_id])

    payload = {
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya@gmail.com",
        "group_leader_id": group_leader_id,
        "bookstore_id": bookstore_id,
    }
    created = integration_client.post("/sellers", json=payload).json()
    seller_id = created["seller_id"]

    response = integration_client.get(f"/sellers/{seller_id}")

    assert response.status_code == 200
    assert response.json()["seller_id"] == seller_id
    assert response.json()["email"] == "priya@gmail.com"


def test_get_seller_returns_404_for_unknown_id(integration_client):
    """GET /sellers/{seller_id} should return 404 for an unknown seller_id."""
    response = integration_client.get("/sellers/nonexistent-id")

    assert response.status_code == 404
    assert "nonexistent-id" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /lookup/group-leaders — integration tests
# ---------------------------------------------------------------------------


def test_lookup_group_leaders_returns_leaders_with_bookstores(
    integration_client, bookstore_table, group_leaders_table
):
    """GET /lookup/group-leaders should return all leaders with their bookstores."""
    bookstore_id = _seed_bookstore(bookstore_table)
    _seed_group_leader(group_leaders_table, [bookstore_id])

    response = integration_client.get("/lookup/group-leaders")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Ravi Kumar"
    assert len(data[0]["bookstores"]) == 1
    assert data[0]["bookstores"][0]["bookstore_id"] == bookstore_id
    assert data[0]["bookstores"][0]["store_name"] == "Sri Lakshmi Books"


def test_lookup_group_leaders_returns_empty_when_none_exist(integration_client):
    """GET /lookup/group-leaders should return empty list when no data exists."""
    response = integration_client.get("/lookup/group-leaders")

    assert response.status_code == 200
    assert response.json() == []
