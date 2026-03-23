"""Unit tests for the Sellers router.

Verifies HTTP behaviour using FastAPI TestClient with a mocked
AbstractSellerService injected via Depends(). No repository, no DynamoDB,
no moto required.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.exceptions.conflict import DuplicateEmailError
from bookrover.exceptions.not_found import (
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
    SellerNotFoundError,
)
from bookrover.interfaces.abstract_seller_service import AbstractSellerService
from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.models.seller import SellerResponse
from bookrover.routers.auth import get_current_user
from bookrover.routers.sellers import get_seller_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


# Authenticated user who owns sel-001 and matches the registration email
SELLER_ME = MeResponse(
    email="priya@gmail.com", roles=["seller"], seller_id="sel-001"
)
# New user (no role yet) who is registering
NEW_USER_ME = MeResponse(email="priya@gmail.com", roles=[])
ADMIN_ME = MeResponse(email="admin@example.com", roles=["admin"])


@pytest.fixture
def mock_service():
    """Mock AbstractSellerService."""
    return MagicMock(spec=AbstractSellerService)


@pytest.fixture
def client(mock_service):
    """TestClient with mock service and a seller user whose email matches SEL-001."""
    app = create_app()
    app.dependency_overrides[get_seller_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: SELLER_ME
    return TestClient(app)


@pytest.fixture
def new_user_client(mock_service):
    """TestClient for a new user (no roles yet) registering as seller."""
    app = create_app()
    app.dependency_overrides[get_seller_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: NEW_USER_ME
    return TestClient(app)


@pytest.fixture
def admin_client(mock_service):
    """TestClient with admin user injected."""
    app = create_app()
    app.dependency_overrides[get_seller_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: ADMIN_ME
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SELLER_RESPONSE = SellerResponse(
    seller_id="sel-001",
    first_name="Priya",
    last_name="Sharma",
    email="priya@gmail.com",
    group_leader_id="gl-001",
    bookstore_id="bs-001",
    status="active",
    created_at="2026-01-01T00:00:00Z",
    updated_at="2026-01-01T00:00:00Z",
)

REGISTER_PAYLOAD = {
    "first_name": "Priya",
    "last_name": "Sharma",
    "email": "priya@gmail.com",
    "group_leader_id": "gl-001",
    "bookstore_id": "bs-001",
}


# ---------------------------------------------------------------------------
# POST /sellers
# ---------------------------------------------------------------------------


def test_register_seller_returns_201(new_user_client, mock_service):
    """POST /sellers should return 201 for an authenticated user registering their own email."""
    mock_service.register_seller.return_value = SELLER_RESPONSE

    response = new_user_client.post("/sellers", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["seller_id"] == "sel-001"
    assert data["first_name"] == "Priya"
    assert data["status"] == "active"


def test_register_seller_returns_409_for_duplicate_email(new_user_client, mock_service):
    """POST /sellers should return 409 when the email is already registered."""
    mock_service.register_seller.side_effect = DuplicateEmailError("priya@gmail.com")

    response = new_user_client.post("/sellers", json=REGISTER_PAYLOAD)

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_register_seller_returns_404_for_unknown_group_leader(new_user_client, mock_service):
    """POST /sellers should return 404 when group_leader_id is not found."""
    mock_service.register_seller.side_effect = GroupLeaderNotFoundError("gl-999")

    response = new_user_client.post("/sellers", json=REGISTER_PAYLOAD)

    assert response.status_code == 404
    assert "gl-999" in response.json()["detail"]


def test_register_seller_returns_404_for_unknown_bookstore(new_user_client, mock_service):
    """POST /sellers should return 404 when bookstore_id is not found."""
    mock_service.register_seller.side_effect = BookStoreNotFoundError("bs-999")

    response = new_user_client.post("/sellers", json=REGISTER_PAYLOAD)

    assert response.status_code == 404
    assert "bs-999" in response.json()["detail"]


def test_register_seller_returns_422_for_missing_fields(new_user_client, mock_service):
    """POST /sellers should return 422 when required fields are missing."""
    response = new_user_client.post("/sellers", json={"first_name": "Priya"})

    assert response.status_code == 422


def test_register_seller_returns_422_for_invalid_email(new_user_client, mock_service):
    """POST /sellers should return 422 for a malformed email address."""
    payload = {**REGISTER_PAYLOAD, "email": "not-an-email"}

    response = new_user_client.post("/sellers", json=payload)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}
# ---------------------------------------------------------------------------


def test_get_seller_returns_200(client, mock_service):
    """GET /sellers/{seller_id} should return 200 and the seller profile."""
    mock_service.get_seller.return_value = SELLER_RESPONSE

    response = client.get("/sellers/sel-001")

    assert response.status_code == 200
    data = response.json()
    assert data["seller_id"] == "sel-001"
    assert data["email"] == "priya@gmail.com"


def test_get_seller_returns_404_for_unknown_id(client, mock_service):
    """GET /sellers/{seller_id} should return 404 when seller does not exist."""
    mock_service.get_seller.side_effect = SellerNotFoundError("nonexistent")

    response = client.get("/sellers/sel-001")

    assert response.status_code == 404
    assert "nonexistent" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Auth enforcement tests
# ---------------------------------------------------------------------------


def test_sellers_endpoint_returns_401_without_auth():
    """Endpoints must return 401 when no Authorization header is present."""
    app = create_app()
    c = TestClient(app)
    response = c.get("/sellers/sel-001")
    assert response.status_code == 401


def test_register_seller_returns_403_when_email_does_not_match_caller(mock_service):
    """POST /sellers must return 403 if payload email differs from the caller's token email."""
    different_user = MeResponse(email="someone.else@example.com", roles=[])
    app = create_app()
    app.dependency_overrides[get_seller_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: different_user
    c = TestClient(app)
    response = c.post("/sellers", json=REGISTER_PAYLOAD)  # payload email is priya@gmail.com
    assert response.status_code == 403


def test_get_seller_returns_403_for_different_seller_id(client, mock_service):
    """GET /sellers/{seller_id} must return 403 when a seller calls for a different seller_id."""
    # client fixture has SELLER_ME with seller_id="sel-001"
    response = client.get("/sellers/sel-DIFFERENT")
    assert response.status_code == 403


def test_get_seller_returns_200_for_admin_reading_any_seller(admin_client, mock_service):
    """Admin can read any seller profile."""
    mock_service.get_seller.return_value = SELLER_RESPONSE
    response = admin_client.get("/sellers/sel-001")
    assert response.status_code == 200
