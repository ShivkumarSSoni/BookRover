"""Unit tests for DashboardService.

Verifies all business logic using mocked repository ABCs.
No DynamoDB, no HTTP, no moto required.
"""

from unittest.mock import MagicMock

import pytest

from bookrover.exceptions.not_found import BookStoreNotFoundError, GroupLeaderNotFoundError
from bookrover.services.dashboard_service import DashboardService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def group_leader_repo():
    """Mock AbstractGroupLeaderRepository."""
    return MagicMock()


@pytest.fixture
def bookstore_repo():
    """Mock AbstractBookstoreRepository."""
    return MagicMock()


@pytest.fixture
def seller_repo():
    """Mock AbstractSellerRepository."""
    return MagicMock()


@pytest.fixture
def sale_repo():
    """Mock AbstractSaleRepository."""
    return MagicMock()


@pytest.fixture
def service(group_leader_repo, bookstore_repo, seller_repo, sale_repo):
    """DashboardService wired with mock repositories."""
    return DashboardService(
        group_leader_repository=group_leader_repo,
        bookstore_repository=bookstore_repo,
        seller_repository=seller_repo,
        sale_repository=sale_repo,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GROUP_LEADER_ITEM = {
    "group_leader_id": "gl-001",
    "name": "Ravi Kumar",
    "email": "ravi@gmail.com",
    "bookstore_ids": ["bs-001", "bs-002"],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

BOOKSTORE_ITEM = {
    "bookstore_id": "bs-001",
    "store_name": "Sri Lakshmi Books",
    "owner_name": "Lakshmi Devi",
    "address": "12 MG Road",
    "phone_number": "+919876543210",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

SELLER_ANAND = {
    "seller_id": "sel-001",
    "first_name": "Anand",
    "last_name": "Raj",
    "bookstore_id": "bs-001",
    "group_leader_id": "gl-001",
    "status": "active",
}

SELLER_PRIYA = {
    "seller_id": "sel-002",
    "first_name": "Priya",
    "last_name": "Nair",
    "bookstore_id": "bs-001",
    "group_leader_id": "gl-001",
    "status": "active",
}

SELLER_OTHER_BOOKSTORE = {
    "seller_id": "sel-003",
    "first_name": "Suresh",
    "last_name": "Kumar",
    "bookstore_id": "bs-002",  # Different bookstore
    "group_leader_id": "gl-001",
    "status": "active",
}

ANAND_SALE = {
    "sale_id": "sale-001",
    "seller_id": "sel-001",
    "total_books_sold": 25,
    "total_amount_collected": 1875.0,
}

PRIYA_SALE = {
    "sale_id": "sale-002",
    "seller_id": "sel-002",
    "total_books_sold": 18,
    "total_amount_collected": 1350.0,
}


def _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo):
    """Set up standard mock return values."""
    group_leader_repo.get_by_id.return_value = GROUP_LEADER_ITEM
    bookstore_repo.get_by_id.return_value = BOOKSTORE_ITEM
    seller_repo.list_by_group_leader.return_value = [SELLER_ANAND, SELLER_PRIYA]
    sale_repo.list_by_seller.side_effect = lambda sid: (
        [ANAND_SALE] if sid == "sel-001" else [PRIYA_SALE]
    )


# ---------------------------------------------------------------------------
# get_dashboard — success path
# ---------------------------------------------------------------------------


def test_get_dashboard_returns_response_with_correct_structure(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard returns DashboardResponse with all required fields."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")

    assert result.group_leader.group_leader_id == "gl-001"
    assert result.group_leader.name == "Ravi Kumar"
    assert result.bookstore.bookstore_id == "bs-001"
    assert result.bookstore.store_name == "Sri Lakshmi Books"
    assert len(result.sellers) == 2


def test_get_dashboard_computes_correct_totals(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard aggregates totals correctly across all sellers."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")

    assert result.totals.total_books_sold == 43
    assert result.totals.total_amount_collected == 3225.0


def test_get_dashboard_computes_per_seller_totals_from_sales(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard sums total_books_sold and total_amount_collected per seller."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)
    # Anand has 2 sales
    sale_repo.list_by_seller.side_effect = lambda sid: (
        [
            {"total_books_sold": 10, "total_amount_collected": 750.0},
            {"total_books_sold": 15, "total_amount_collected": 1125.0},
        ]
        if sid == "sel-001"
        else [PRIYA_SALE]
    )

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")

    anand = next(r for r in result.sellers if r.seller_id == "sel-001")
    assert anand.total_books_sold == 25
    assert anand.total_amount_collected == 1875.0


def test_get_dashboard_sorts_desc_by_total_amount_collected(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard sorts sellers by total_amount_collected descending by default."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")

    assert result.sellers[0].total_amount_collected >= result.sellers[1].total_amount_collected


def test_get_dashboard_sorts_asc_by_total_amount_collected(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard sorts ascending when sort_order='asc'."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "asc")

    assert result.sellers[0].total_amount_collected <= result.sellers[1].total_amount_collected


def test_get_dashboard_sorts_by_total_books_sold(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard sorts sellers by total_books_sold when requested."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)

    result = service.get_dashboard("gl-001", "bs-001", "total_books_sold", "desc")

    assert result.sellers[0].total_books_sold >= result.sellers[1].total_books_sold


def test_get_dashboard_filters_sellers_to_bookstore(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard only includes sellers for the selected bookstore."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)
    seller_repo.list_by_group_leader.return_value = [
        SELLER_ANAND,
        SELLER_PRIYA,
        SELLER_OTHER_BOOKSTORE,  # belongs to bs-002 — should be excluded
    ]
    sale_repo.list_by_seller.return_value = []

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")

    seller_ids = {r.seller_id for r in result.sellers}
    assert "sel-003" not in seller_ids
    assert len(result.sellers) == 2


def test_get_dashboard_builds_full_name_from_first_and_last(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard constructs full_name as 'first_name last_name'."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")

    names = {r.full_name for r in result.sellers}
    assert "Anand Raj" in names
    assert "Priya Nair" in names


def test_get_dashboard_handles_seller_with_no_sales(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard includes sellers with zero sales (totals = 0)."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)
    sale_repo.list_by_seller.side_effect = None
    sale_repo.list_by_seller.return_value = []

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")

    for row in result.sellers:
        assert row.total_books_sold == 0
        assert row.total_amount_collected == 0.0

    assert result.totals.total_books_sold == 0
    assert result.totals.total_amount_collected == 0.0


def test_get_dashboard_returns_empty_sellers_when_no_sellers(
    service, group_leader_repo, bookstore_repo, seller_repo, sale_repo
):
    """get_dashboard returns empty sellers list when no sellers are registered."""
    _setup_defaults(group_leader_repo, bookstore_repo, seller_repo, sale_repo)
    seller_repo.list_by_group_leader.return_value = []
    sale_repo.list_by_seller.side_effect = None
    sale_repo.list_by_seller.return_value = []

    result = service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")

    assert result.sellers == []
    assert result.totals.total_books_sold == 0


# ---------------------------------------------------------------------------
# get_dashboard — error paths
# ---------------------------------------------------------------------------


def test_get_dashboard_raises_group_leader_not_found(service, group_leader_repo):
    """get_dashboard raises GroupLeaderNotFoundError when group leader does not exist."""
    group_leader_repo.get_by_id.return_value = None

    with pytest.raises(GroupLeaderNotFoundError):
        service.get_dashboard("no-gl", "bs-001", "total_amount_collected", "desc")


def test_get_dashboard_raises_bookstore_not_found_if_not_in_list(
    service, group_leader_repo
):
    """get_dashboard raises BookStoreNotFoundError when bookstore is not linked to group leader."""
    group_leader_repo.get_by_id.return_value = {
        **GROUP_LEADER_ITEM,
        "bookstore_ids": ["bs-999"],  # bs-001 not in this list
    }

    with pytest.raises(BookStoreNotFoundError):
        service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")


def test_get_dashboard_raises_bookstore_not_found_if_missing_from_db(
    service, group_leader_repo, bookstore_repo
):
    """get_dashboard raises BookStoreNotFoundError when bookstore missing from DB."""
    group_leader_repo.get_by_id.return_value = GROUP_LEADER_ITEM
    bookstore_repo.get_by_id.return_value = None

    with pytest.raises(BookStoreNotFoundError):
        service.get_dashboard("gl-001", "bs-001", "total_amount_collected", "desc")
