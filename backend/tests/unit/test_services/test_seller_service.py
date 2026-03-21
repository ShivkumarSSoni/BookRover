"""Unit tests for SellerService.

Verifies all business logic in SellerService using mocked repository
ABCs. No DynamoDB, no HTTP, no moto required.
"""

from unittest.mock import MagicMock

import pytest

from bookrover.exceptions.conflict import DuplicateEmailError
from bookrover.exceptions.not_found import (
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
    SellerNotFoundError,
)
from bookrover.models.seller import SellerCreate
from bookrover.services.seller_service import SellerService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seller_repo():
    """Mock AbstractSellerRepository."""
    return MagicMock()


@pytest.fixture
def group_leader_repo():
    """Mock AbstractGroupLeaderRepository."""
    return MagicMock()


@pytest.fixture
def bookstore_repo():
    """Mock AbstractBookstoreRepository."""
    return MagicMock()


@pytest.fixture
def service(seller_repo, group_leader_repo, bookstore_repo):
    """SellerService wired with mock repositories."""
    return SellerService(
        seller_repository=seller_repo,
        group_leader_repository=group_leader_repo,
        bookstore_repository=bookstore_repo,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SELLER_PAYLOAD = SellerCreate(
    first_name="Priya",
    last_name="Sharma",
    email="priya@gmail.com",
    group_leader_id="gl-001",
    bookstore_id="bs-001",
)

SELLER_ITEM = {
    "seller_id": "sel-001",
    "first_name": "Priya",
    "last_name": "Sharma",
    "email": "priya@gmail.com",
    "group_leader_id": "gl-001",
    "bookstore_id": "bs-001",
    "status": "active",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

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
# register_seller — happy path
# ---------------------------------------------------------------------------


def test_register_seller_returns_seller_response(service, seller_repo, group_leader_repo, bookstore_repo):
    """register_seller should verify uniqueness, validate references, and return SellerResponse."""
    seller_repo.get_by_email.return_value = None
    group_leader_repo.get_by_id.return_value = GROUP_LEADER_ITEM
    bookstore_repo.get_by_id.return_value = BOOKSTORE_ITEM
    seller_repo.create.return_value = SELLER_ITEM

    result = service.register_seller(SELLER_PAYLOAD)

    seller_repo.get_by_email.assert_called_once_with("priya@gmail.com")
    group_leader_repo.get_by_id.assert_called_once_with("gl-001")
    bookstore_repo.get_by_id.assert_called_once_with("bs-001")
    seller_repo.create.assert_called_once()
    assert result.seller_id == "sel-001"
    assert result.first_name == "Priya"
    assert result.status == "active"


def test_register_seller_sets_status_active(service, seller_repo, group_leader_repo, bookstore_repo):
    """register_seller must persist status='active' in the created item."""
    seller_repo.get_by_email.return_value = None
    group_leader_repo.get_by_id.return_value = GROUP_LEADER_ITEM
    bookstore_repo.get_by_id.return_value = BOOKSTORE_ITEM
    seller_repo.create.return_value = SELLER_ITEM

    service.register_seller(SELLER_PAYLOAD)

    created_item = seller_repo.create.call_args[0][0]
    assert created_item["status"] == "active"


def test_register_seller_sets_timestamps(service, seller_repo, group_leader_repo, bookstore_repo):
    """register_seller must add created_at and updated_at to the item."""
    seller_repo.get_by_email.return_value = None
    group_leader_repo.get_by_id.return_value = GROUP_LEADER_ITEM
    bookstore_repo.get_by_id.return_value = BOOKSTORE_ITEM
    seller_repo.create.return_value = SELLER_ITEM

    service.register_seller(SELLER_PAYLOAD)

    created_item = seller_repo.create.call_args[0][0]
    assert "created_at" in created_item
    assert "updated_at" in created_item


# ---------------------------------------------------------------------------
# register_seller — error cases
# ---------------------------------------------------------------------------


def test_register_seller_raises_duplicate_email(service, seller_repo):
    """register_seller should raise DuplicateEmailError if email is already taken."""
    seller_repo.get_by_email.return_value = SELLER_ITEM

    with pytest.raises(DuplicateEmailError):
        service.register_seller(SELLER_PAYLOAD)

    seller_repo.create.assert_not_called()


def test_register_seller_raises_group_leader_not_found(service, seller_repo, group_leader_repo):
    """register_seller should raise GroupLeaderNotFoundError for unknown group_leader_id."""
    seller_repo.get_by_email.return_value = None
    group_leader_repo.get_by_id.return_value = None

    with pytest.raises(GroupLeaderNotFoundError):
        service.register_seller(SELLER_PAYLOAD)

    seller_repo.create.assert_not_called()


def test_register_seller_raises_bookstore_not_found(service, seller_repo, group_leader_repo, bookstore_repo):
    """register_seller should raise BookStoreNotFoundError for unknown bookstore_id."""
    seller_repo.get_by_email.return_value = None
    group_leader_repo.get_by_id.return_value = GROUP_LEADER_ITEM
    bookstore_repo.get_by_id.return_value = None

    with pytest.raises(BookStoreNotFoundError):
        service.register_seller(SELLER_PAYLOAD)

    seller_repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# get_seller
# ---------------------------------------------------------------------------


def test_get_seller_returns_seller_response(service, seller_repo):
    """get_seller should return a SellerResponse for an existing seller."""
    seller_repo.get_by_id.return_value = SELLER_ITEM

    result = service.get_seller("sel-001")

    seller_repo.get_by_id.assert_called_once_with("sel-001")
    assert result.seller_id == "sel-001"
    assert result.email == "priya@gmail.com"


def test_get_seller_raises_seller_not_found(service, seller_repo):
    """get_seller should raise SellerNotFoundError if seller does not exist."""
    seller_repo.get_by_id.return_value = None

    with pytest.raises(SellerNotFoundError):
        service.get_seller("nonexistent-id")
