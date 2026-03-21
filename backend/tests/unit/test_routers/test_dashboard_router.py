"""Unit tests for the Dashboard router.

Verifies HTTP behaviour using FastAPI TestClient with a mocked
AbstractDashboardService injected via Depends(). No repository, no DynamoDB,
no moto required.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.exceptions.not_found import BookStoreNotFoundError, GroupLeaderNotFoundError
from bookrover.interfaces.abstract_dashboard_service import AbstractDashboardService
from bookrover.main import create_app
from bookrover.models.dashboard import (
    DashboardBookstore,
    DashboardGroupLeader,
    DashboardResponse,
    DashboardSellerRow,
    DashboardTotals,
)
from bookrover.routers.dashboard import get_dashboard_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    """Mock AbstractDashboardService."""
    return MagicMock(spec=AbstractDashboardService)


@pytest.fixture
def client(mock_service):
    """TestClient with the mock service injected via dependency override."""
    app = create_app()
    app.dependency_overrides[get_dashboard_service] = lambda: mock_service
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DASHBOARD_RESPONSE = DashboardResponse(
    group_leader=DashboardGroupLeader(group_leader_id="gl-001", name="Ravi Kumar"),
    bookstore=DashboardBookstore(bookstore_id="bs-001", store_name="Sri Lakshmi Books"),
    sellers=[
        DashboardSellerRow(
            seller_id="sel-001",
            full_name="Anand Raj",
            total_books_sold=25,
            total_amount_collected=1875.0,
        ),
        DashboardSellerRow(
            seller_id="sel-002",
            full_name="Priya Nair",
            total_books_sold=18,
            total_amount_collected=1350.0,
        ),
    ],
    totals=DashboardTotals(total_books_sold=43, total_amount_collected=3225.0),
)

BASE_URL = "/group-leaders/gl-001/dashboard?bookstore_id=bs-001"


# ---------------------------------------------------------------------------
# GET /group-leaders/{id}/dashboard
# ---------------------------------------------------------------------------


def test_get_dashboard_returns_200_with_all_fields(client, mock_service):
    """GET /group-leaders/{id}/dashboard should return 200 with full response."""
    mock_service.get_dashboard.return_value = DASHBOARD_RESPONSE

    response = client.get(BASE_URL)

    assert response.status_code == 200
    data = response.json()
    assert data["group_leader"]["group_leader_id"] == "gl-001"
    assert data["group_leader"]["name"] == "Ravi Kumar"
    assert data["bookstore"]["store_name"] == "Sri Lakshmi Books"
    assert len(data["sellers"]) == 2
    assert data["totals"]["total_books_sold"] == 43
    assert data["totals"]["total_amount_collected"] == 3225.0


def test_get_dashboard_uses_default_sort(client, mock_service):
    """GET /group-leaders/{id}/dashboard uses default sort when not specified."""
    mock_service.get_dashboard.return_value = DASHBOARD_RESPONSE

    client.get(BASE_URL)

    mock_service.get_dashboard.assert_called_once_with(
        "gl-001", "bs-001", "total_amount_collected", "desc"
    )


def test_get_dashboard_passes_sort_params_to_service(client, mock_service):
    """GET /group-leaders/{id}/dashboard forwards sort_by and sort_order to service."""
    mock_service.get_dashboard.return_value = DASHBOARD_RESPONSE

    client.get(f"{BASE_URL}&sort_by=total_books_sold&sort_order=asc")

    mock_service.get_dashboard.assert_called_once_with(
        "gl-001", "bs-001", "total_books_sold", "asc"
    )


def test_get_dashboard_returns_422_for_invalid_sort_by(client, mock_service):
    """GET /group-leaders/{id}/dashboard returns 422 for unsupported sort_by value."""
    response = client.get(f"{BASE_URL}&sort_by=invalid_field")

    assert response.status_code == 422


def test_get_dashboard_returns_422_for_invalid_sort_order(client, mock_service):
    """GET /group-leaders/{id}/dashboard returns 422 for unsupported sort_order value."""
    response = client.get(f"{BASE_URL}&sort_order=random")

    assert response.status_code == 422


def test_get_dashboard_returns_422_when_bookstore_id_missing(client, mock_service):
    """GET /group-leaders/{id}/dashboard returns 422 when bookstore_id is missing."""
    response = client.get("/group-leaders/gl-001/dashboard")

    assert response.status_code == 422


def test_get_dashboard_returns_404_for_unknown_group_leader(client, mock_service):
    """GET /group-leaders/{id}/dashboard returns 404 if group leader not found."""
    mock_service.get_dashboard.side_effect = GroupLeaderNotFoundError("gl-unknown")

    response = client.get(BASE_URL)

    assert response.status_code == 404
    assert "gl-unknown" in response.json()["detail"]


def test_get_dashboard_returns_404_for_unknown_bookstore(client, mock_service):
    """GET /group-leaders/{id}/dashboard returns 404 if bookstore not found or not linked."""
    mock_service.get_dashboard.side_effect = BookStoreNotFoundError("bs-unknown")

    response = client.get(BASE_URL)

    assert response.status_code == 404
    assert "bs-unknown" in response.json()["detail"]


def test_get_dashboard_returns_empty_sellers_list(client, mock_service):
    """GET /group-leaders/{id}/dashboard returns empty sellers list correctly."""
    mock_service.get_dashboard.return_value = DashboardResponse(
        group_leader=DashboardGroupLeader(group_leader_id="gl-001", name="Ravi Kumar"),
        bookstore=DashboardBookstore(bookstore_id="bs-001", store_name="Sri Lakshmi Books"),
        sellers=[],
        totals=DashboardTotals(total_books_sold=0, total_amount_collected=0.0),
    )

    response = client.get(BASE_URL)

    assert response.status_code == 200
    data = response.json()
    assert data["sellers"] == []
    assert data["totals"]["total_books_sold"] == 0
