"""Unit tests for the Admin router.

Verifies HTTP behaviour using FastAPI TestClient with a mocked
AbstractAdminService injected via Depends(). No repository, no DynamoDB,
no moto required.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.exceptions.conflict import ActiveSellersExistError, DuplicateEmailError
from bookrover.exceptions.not_found import (
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
)
from bookrover.interfaces.abstract_admin_service import AbstractAdminService
from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.models.bookstore import BookStoreResponse
from bookrover.models.group_leader import GroupLeaderResponse
from bookrover.routers.admin import get_admin_service
from bookrover.routers.auth import get_current_user

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


ADMIN_ME = MeResponse(email="admin@example.com", roles=["admin"])
SELLER_ME = MeResponse(email="seller@example.com", roles=["seller"], seller_id="sel-001")


@pytest.fixture
def mock_service():
    """Mock AbstractAdminService."""
    return MagicMock(spec=AbstractAdminService)


@pytest.fixture
def client(mock_service):
    """TestClient with the mock service and admin user injected."""
    app = create_app()
    app.dependency_overrides[get_admin_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: ADMIN_ME
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOOKSTORE_RESPONSE = BookStoreResponse(
    bookstore_id="bs-001",
    store_name="Sri Lakshmi Books",
    owner_name="Lakshmi Devi",
    address="12 MG Road, Chennai",
    phone_number="+914423456789",
    created_at="2026-01-01T00:00:00Z",
    updated_at="2026-01-01T00:00:00Z",
)

GROUP_LEADER_RESPONSE = GroupLeaderResponse(
    group_leader_id="gl-001",
    name="Ravi Kumar",
    email="ravi@gmail.com",
    bookstore_ids=["bs-001"],
    created_at="2026-01-01T00:00:00Z",
    updated_at="2026-01-01T00:00:00Z",
)

BOOKSTORE_PAYLOAD = {
    "store_name": "Sri Lakshmi Books",
    "owner_name": "Lakshmi Devi",
    "address": "12 MG Road, Chennai",
    "phone_number": "+914423456789",
}

GROUP_LEADER_PAYLOAD = {
    "name": "Ravi Kumar",
    "email": "ravi@gmail.com",
    "bookstore_ids": ["bs-001"],
}


# ---------------------------------------------------------------------------
# BookStore router tests
# ---------------------------------------------------------------------------


def test_create_bookstore_returns_201(client, mock_service):
    """POST /admin/bookstores should return 201 and the created bookstore."""
    mock_service.create_bookstore.return_value = BOOKSTORE_RESPONSE

    response = client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["bookstore_id"] == "bs-001"
    assert data["store_name"] == "Sri Lakshmi Books"


def test_create_bookstore_validates_missing_fields(client, mock_service):
    """POST /admin/bookstores should return 422 for missing required fields."""
    response = client.post("/admin/bookstores", json={"store_name": "Only Name"})

    assert response.status_code == 422


def test_list_bookstores_returns_200(client, mock_service):
    """GET /admin/bookstores should return 200 with list of bookstores."""
    mock_service.list_bookstores.return_value = [BOOKSTORE_RESPONSE]

    response = client.get("/admin/bookstores")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["bookstore_id"] == "bs-001"


def test_list_bookstores_returns_empty_list(client, mock_service):
    """GET /admin/bookstores should return 200 with empty list when no bookstores exist."""
    mock_service.list_bookstores.return_value = []

    response = client.get("/admin/bookstores")

    assert response.status_code == 200
    assert response.json() == []


def test_update_bookstore_returns_200(client, mock_service):
    """PUT /admin/bookstores/{id} should return 200 with the updated bookstore."""
    mock_service.update_bookstore.return_value = BOOKSTORE_RESPONSE

    response = client.put("/admin/bookstores/bs-001", json={"owner_name": "New Owner"})

    assert response.status_code == 200
    assert response.json()["bookstore_id"] == "bs-001"


def test_update_bookstore_returns_404_when_not_found(client, mock_service):
    """PUT /admin/bookstores/{id} should return 404 when bookstore does not exist."""
    mock_service.update_bookstore.side_effect = BookStoreNotFoundError("bs-999")

    response = client.put("/admin/bookstores/bs-999", json={"owner_name": "Ghost"})

    assert response.status_code == 404
    assert "bs-999" in response.json()["detail"]


def test_delete_bookstore_returns_204(client, mock_service):
    """DELETE /admin/bookstores/{id} should return 204 on successful deletion."""
    mock_service.delete_bookstore.return_value = None

    response = client.delete("/admin/bookstores/bs-001")

    assert response.status_code == 204


def test_delete_bookstore_returns_404_when_not_found(client, mock_service):
    """DELETE /admin/bookstores/{id} should return 404 when bookstore does not exist."""
    mock_service.delete_bookstore.side_effect = BookStoreNotFoundError("bs-999")

    response = client.delete("/admin/bookstores/bs-999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GroupLeader router tests
# ---------------------------------------------------------------------------


def test_create_group_leader_returns_201(client, mock_service):
    """POST /admin/group-leaders should return 201 and the created group leader."""
    mock_service.create_group_leader.return_value = GROUP_LEADER_RESPONSE

    response = client.post("/admin/group-leaders", json=GROUP_LEADER_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["group_leader_id"] == "gl-001"
    assert data["email"] == "ravi@gmail.com"


def test_create_group_leader_returns_409_on_duplicate_email(client, mock_service):
    """POST /admin/group-leaders should return 409 when email is already registered."""
    mock_service.create_group_leader.side_effect = DuplicateEmailError("ravi@gmail.com")

    response = client.post("/admin/group-leaders", json=GROUP_LEADER_PAYLOAD)

    assert response.status_code == 409
    assert "ravi@gmail.com" in response.json()["detail"]


def test_create_group_leader_validates_invalid_email(client, mock_service):
    """POST /admin/group-leaders should return 422 for invalid email format."""
    invalid_payload = {**GROUP_LEADER_PAYLOAD, "email": "not-an-email"}

    response = client.post("/admin/group-leaders", json=invalid_payload)

    assert response.status_code == 422


def test_list_group_leaders_returns_200(client, mock_service):
    """GET /admin/group-leaders should return 200 with list of group leaders."""
    mock_service.list_group_leaders.return_value = [GROUP_LEADER_RESPONSE]

    response = client.get("/admin/group-leaders")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Ravi Kumar"


def test_update_group_leader_returns_200(client, mock_service):
    """PUT /admin/group-leaders/{id} should return 200 with updated group leader."""
    mock_service.update_group_leader.return_value = GROUP_LEADER_RESPONSE

    response = client.put("/admin/group-leaders/gl-001", json={"name": "Ravi K"})

    assert response.status_code == 200


def test_update_group_leader_returns_404_when_not_found(client, mock_service):
    """PUT /admin/group-leaders/{id} should return 404 when group leader does not exist."""
    mock_service.update_group_leader.side_effect = GroupLeaderNotFoundError("gl-999")

    response = client.put("/admin/group-leaders/gl-999", json={"name": "Ghost"})

    assert response.status_code == 404
    assert "gl-999" in response.json()["detail"]


def test_delete_group_leader_returns_204(client, mock_service):
    """DELETE /admin/group-leaders/{id} should return 204 on successful deletion."""
    mock_service.delete_group_leader.return_value = None

    response = client.delete("/admin/group-leaders/gl-001")

    assert response.status_code == 204


def test_delete_group_leader_returns_409_when_active_sellers_exist(client, mock_service):
    """DELETE /admin/group-leaders/{id} should return 409 when sellers are assigned."""
    mock_service.delete_group_leader.side_effect = ActiveSellersExistError("gl-001", 3)

    response = client.delete("/admin/group-leaders/gl-001")

    assert response.status_code == 409
    assert "gl-001" in response.json()["detail"]


def test_delete_group_leader_returns_404_when_not_found(client, mock_service):
    """DELETE /admin/group-leaders/{id} should return 404 when group leader does not exist."""
    mock_service.delete_group_leader.side_effect = GroupLeaderNotFoundError("gl-999")

    response = client.delete("/admin/group-leaders/gl-999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Auth enforcement tests
# ---------------------------------------------------------------------------


def test_admin_endpoint_returns_401_without_auth():
    """Admin endpoints must return 401 when no Authorization header is present."""
    app = create_app()
    c = TestClient(app)
    response = c.get("/admin/bookstores")
    assert response.status_code == 401


def test_admin_endpoint_returns_403_for_seller_role():
    """Admin endpoints must return 403 when the caller has the seller role (not admin)."""
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: SELLER_ME
    c = TestClient(app)
    response = c.get("/admin/bookstores")
    assert response.status_code == 403


def test_admin_endpoint_returns_403_for_group_leader_role():
    """Admin endpoints must return 403 when the caller has the group_leader role (not admin)."""
    gl_me = MeResponse(email="gl@example.com", roles=["group_leader"], group_leader_id="gl-001")
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: gl_me
    c = TestClient(app)
    response = c.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    assert response.status_code == 403
