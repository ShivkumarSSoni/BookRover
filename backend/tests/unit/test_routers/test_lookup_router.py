"""Unit tests for the Lookup router.

Verifies HTTP behaviour using FastAPI TestClient with mocked repositories
injected via Depends(). No DynamoDB, no moto required.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.main import create_app
from bookrover.routers.lookup import get_lookup_repos

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_gl_repo():
    """Mock AbstractGroupLeaderRepository."""
    return MagicMock()


@pytest.fixture
def mock_bs_repo():
    """Mock AbstractBookstoreRepository."""
    return MagicMock()


@pytest.fixture
def client(mock_gl_repo, mock_bs_repo):
    """TestClient with mocked repos injected via dependency override."""
    app = create_app()
    app.dependency_overrides[get_lookup_repos] = lambda: (mock_gl_repo, mock_bs_repo)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GROUP_LEADER_ITEM = {
    "group_leader_id": "gl-001",
    "name": "Ravi Kumar",
    "email": "ravi@gmail.com",
    "bookstore_ids": ["bs-001"],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

BOOKSTORE_ITEM = {
    "bookstore_id": "bs-001",
    "store_name": "Sri Lakshmi Books",
    "owner_name": "Lakshmi Devi",
    "address": "12 MG Road, Chennai",
    "phone_number": "+914423456789",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}


# ---------------------------------------------------------------------------
# GET /lookup/group-leaders
# ---------------------------------------------------------------------------


def test_list_group_leaders_returns_200(client, mock_gl_repo, mock_bs_repo):
    """GET /lookup/group-leaders should return 200 with all group leaders."""
    mock_bs_repo.list_all.return_value = [BOOKSTORE_ITEM]
    mock_gl_repo.list_all.return_value = [GROUP_LEADER_ITEM]

    response = client.get("/lookup/group-leaders")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["group_leader_id"] == "gl-001"
    assert data[0]["name"] == "Ravi Kumar"


def test_list_group_leaders_maps_bookstores(client, mock_gl_repo, mock_bs_repo):
    """GET /lookup/group-leaders should embed bookstore name and id for each leader."""
    mock_bs_repo.list_all.return_value = [BOOKSTORE_ITEM]
    mock_gl_repo.list_all.return_value = [GROUP_LEADER_ITEM]

    response = client.get("/lookup/group-leaders")

    bookstores = response.json()[0]["bookstores"]
    assert len(bookstores) == 1
    assert bookstores[0]["bookstore_id"] == "bs-001"
    assert bookstores[0]["store_name"] == "Sri Lakshmi Books"


def test_list_group_leaders_skips_unknown_bookstore_ids(client, mock_gl_repo, mock_bs_repo):
    """Bookstore IDs that don't exist in the bookstore table should be silently skipped."""
    mock_bs_repo.list_all.return_value = []  # no bookstores in table
    leader_with_stale_ids = {**GROUP_LEADER_ITEM, "bookstore_ids": ["stale-bs-id"]}
    mock_gl_repo.list_all.return_value = [leader_with_stale_ids]

    response = client.get("/lookup/group-leaders")

    assert response.status_code == 200
    # Should return the leader but with an empty bookstores list
    assert response.json()[0]["bookstores"] == []


def test_list_group_leaders_returns_empty_when_no_leaders(client, mock_gl_repo, mock_bs_repo):
    """GET /lookup/group-leaders should return an empty list when there are no group leaders."""
    mock_bs_repo.list_all.return_value = []
    mock_gl_repo.list_all.return_value = []

    response = client.get("/lookup/group-leaders")

    assert response.status_code == 200
    assert response.json() == []


def test_list_group_leaders_returns_multiple_leaders(client, mock_gl_repo, mock_bs_repo):
    """GET /lookup/group-leaders should return all group leaders."""
    bs2 = {**BOOKSTORE_ITEM, "bookstore_id": "bs-002", "store_name": "Saraswati Books"}
    gl2 = {
        "group_leader_id": "gl-002",
        "name": "Meera Reddy",
        "email": "meera@gmail.com",
        "bookstore_ids": ["bs-002"],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    mock_bs_repo.list_all.return_value = [BOOKSTORE_ITEM, bs2]
    mock_gl_repo.list_all.return_value = [GROUP_LEADER_ITEM, gl2]

    response = client.get("/lookup/group-leaders")

    assert response.status_code == 200
    assert len(response.json()) == 2
