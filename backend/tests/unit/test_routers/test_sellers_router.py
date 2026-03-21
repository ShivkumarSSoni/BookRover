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
from bookrover.models.seller import SellerResponse
from bookrover.routers.sellers import get_seller_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    """Mock AbstractSellerService."""
    return MagicMock(spec=AbstractSellerService)


@pytest.fixture
def client(mock_service):
    """TestClient with the mock service injected via dependency override."""
    app = create_app()
    app.dependency_overrides[get_seller_service] = lambda: mock_service
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


def test_register_seller_returns_201(client, mock_service):
    """POST /sellers should return 201 and the created seller."""
    mock_service.register_seller.return_value = SELLER_RESPONSE

    response = client.post("/sellers", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["seller_id"] == "sel-001"
    assert data["first_name"] == "Priya"
    assert data["status"] == "active"


def test_register_seller_returns_409_for_duplicate_email(client, mock_service):
    """POST /sellers should return 409 when the email is already registered."""
    mock_service.register_seller.side_effect = DuplicateEmailError("priya@gmail.com")

    response = client.post("/sellers", json=REGISTER_PAYLOAD)

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_register_seller_returns_404_for_unknown_group_leader(client, mock_service):
    """POST /sellers should return 404 when group_leader_id is not found."""
    mock_service.register_seller.side_effect = GroupLeaderNotFoundError("gl-999")

    response = client.post("/sellers", json=REGISTER_PAYLOAD)

    assert response.status_code == 404
    assert "gl-999" in response.json()["detail"]


def test_register_seller_returns_404_for_unknown_bookstore(client, mock_service):
    """POST /sellers should return 404 when bookstore_id is not found."""
    mock_service.register_seller.side_effect = BookStoreNotFoundError("bs-999")

    response = client.post("/sellers", json=REGISTER_PAYLOAD)

    assert response.status_code == 404
    assert "bs-999" in response.json()["detail"]


def test_register_seller_returns_422_for_missing_fields(client, mock_service):
    """POST /sellers should return 422 when required fields are missing."""
    response = client.post("/sellers", json={"first_name": "Priya"})

    assert response.status_code == 422


def test_register_seller_returns_422_for_invalid_email(client, mock_service):
    """POST /sellers should return 422 for a malformed email address."""
    payload = {**REGISTER_PAYLOAD, "email": "not-an-email"}

    response = client.post("/sellers", json=payload)

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

    response = client.get("/sellers/nonexistent")

    assert response.status_code == 404
    assert "nonexistent" in response.json()["detail"]
