"""Unit tests for AdminService.

Verifies all business logic in AdminService using mocked repository
ABCs. No DynamoDB, no HTTP, no moto required.
"""

from unittest.mock import MagicMock

import pytest

from bookrover.exceptions.conflict import ActiveSellersExistError, DuplicateEmailError
from bookrover.exceptions.not_found import (
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
)
from bookrover.models.bookstore import BookStoreCreate, BookStoreUpdate
from bookrover.models.group_leader import GroupLeaderCreate, GroupLeaderUpdate
from bookrover.services.admin_service import AdminService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bookstore_repo():
    """Mock AbstractBookstoreRepository."""
    return MagicMock()


@pytest.fixture
def group_leader_repo():
    """Mock AbstractGroupLeaderRepository."""
    return MagicMock()


@pytest.fixture
def service(bookstore_repo, group_leader_repo):
    """AdminService wired with mock repositories."""
    return AdminService(
        bookstore_repository=bookstore_repo,
        group_leader_repository=group_leader_repo,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOOKSTORE_ITEM = {
    "bookstore_id": "bs-001",
    "store_name": "Sri Lakshmi Books",
    "owner_name": "Lakshmi Devi",
    "address": "12 MG Road, Chennai",
    "phone_number": "+914423456789",
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


# ---------------------------------------------------------------------------
# BookStore unit tests
# ---------------------------------------------------------------------------


def test_create_bookstore_returns_response(service, bookstore_repo):
    """create_bookstore should call repo.create and return a BookStoreResponse."""
    bookstore_repo.create.return_value = BOOKSTORE_ITEM
    payload = BookStoreCreate(
        store_name="Sri Lakshmi Books",
        owner_name="Lakshmi Devi",
        address="12 MG Road, Chennai",
        phone_number="+914423456789",
    )

    result = service.create_bookstore(payload)

    bookstore_repo.create.assert_called_once()
    assert result.bookstore_id == "bs-001"
    assert result.store_name == "Sri Lakshmi Books"


def test_list_bookstores_returns_all(service, bookstore_repo):
    """list_bookstores should return one BookStoreResponse per item."""
    bookstore_repo.list_all.return_value = [BOOKSTORE_ITEM]

    result = service.list_bookstores()

    assert len(result) == 1
    assert result[0].store_name == "Sri Lakshmi Books"


def test_list_bookstores_empty(service, bookstore_repo):
    """list_bookstores should return empty list when no bookstores exist."""
    bookstore_repo.list_all.return_value = []

    result = service.list_bookstores()

    assert result == []


def test_update_bookstore_applies_non_none_fields(service, bookstore_repo):
    """update_bookstore should only pass non-None fields to the repository."""
    updated_item = {**BOOKSTORE_ITEM, "owner_name": "New Owner", "updated_at": "2026-06-01T00:00:00Z"}
    bookstore_repo.update.return_value = updated_item
    payload = BookStoreUpdate(owner_name="New Owner")

    result = service.update_bookstore("bs-001", payload)

    call_fields = bookstore_repo.update.call_args[0][1]
    assert "owner_name" in call_fields
    assert "store_name" not in call_fields
    assert "updated_at" in call_fields
    assert result.owner_name == "New Owner"


def test_update_bookstore_raises_not_found(service, bookstore_repo):
    """update_bookstore should raise BookStoreNotFoundError when repo raises it."""
    bookstore_repo.update.side_effect = BookStoreNotFoundError("bs-999")
    payload = BookStoreUpdate(owner_name="Ghost")

    with pytest.raises(BookStoreNotFoundError):
        service.update_bookstore("bs-999", payload)


def test_update_bookstore_empty_payload_checks_existence(service, bookstore_repo):
    """update_bookstore with no fields should still verify the bookstore exists."""
    bookstore_repo.get_by_id.return_value = BOOKSTORE_ITEM
    payload = BookStoreUpdate()

    result = service.update_bookstore("bs-001", payload)

    bookstore_repo.get_by_id.assert_called_once_with("bs-001")
    bookstore_repo.update.assert_not_called()
    assert result.bookstore_id == "bs-001"


def test_update_bookstore_empty_payload_raises_not_found(service, bookstore_repo):
    """update_bookstore with no fields and unknown ID should raise BookStoreNotFoundError."""
    bookstore_repo.get_by_id.return_value = None
    payload = BookStoreUpdate()

    with pytest.raises(BookStoreNotFoundError):
        service.update_bookstore("bs-999", payload)


def test_delete_bookstore_calls_repo_delete(service, bookstore_repo):
    """delete_bookstore should delegate to repo.delete."""
    service.delete_bookstore("bs-001")

    bookstore_repo.delete.assert_called_once_with("bs-001")


def test_delete_bookstore_raises_not_found(service, bookstore_repo):
    """delete_bookstore should propagate BookStoreNotFoundError from repo."""
    bookstore_repo.delete.side_effect = BookStoreNotFoundError("bs-999")

    with pytest.raises(BookStoreNotFoundError):
        service.delete_bookstore("bs-999")


# ---------------------------------------------------------------------------
# GroupLeader unit tests
# ---------------------------------------------------------------------------


def test_create_group_leader_returns_response(service, group_leader_repo):
    """create_group_leader should normalise email to lowercase and persist the GroupLeader."""
    group_leader_repo.get_by_email.return_value = None
    group_leader_repo.create.return_value = GROUP_LEADER_ITEM
    payload = GroupLeaderCreate(name="Ravi Kumar", email="Ravi@Gmail.com", bookstore_ids=["bs-001"])

    result = service.create_group_leader(payload)

    group_leader_repo.get_by_email.assert_called_once_with("ravi@gmail.com")
    created_item = group_leader_repo.create.call_args[0][0]
    assert created_item["email"] == "ravi@gmail.com"
    assert result.group_leader_id == "gl-001"


def test_create_group_leader_raises_duplicate_email(service, group_leader_repo):
    """create_group_leader should raise DuplicateEmailError when email already exists."""
    group_leader_repo.get_by_email.return_value = GROUP_LEADER_ITEM
    payload = GroupLeaderCreate(name="Ravi Kumar", email="ravi@gmail.com", bookstore_ids=["bs-001"])

    with pytest.raises(DuplicateEmailError):
        service.create_group_leader(payload)

    group_leader_repo.create.assert_not_called()


def test_list_group_leaders_returns_all(service, group_leader_repo):
    """list_group_leaders should return one GroupLeaderResponse per item."""
    group_leader_repo.list_all.return_value = [GROUP_LEADER_ITEM]

    result = service.list_group_leaders()

    assert len(result) == 1
    assert result[0].name == "Ravi Kumar"


def test_update_group_leader_applies_non_none_fields(service, group_leader_repo):
    """update_group_leader should only pass non-None fields to the repository."""
    updated_item = {**GROUP_LEADER_ITEM, "name": "Ravi K", "updated_at": "2026-06-01T00:00:00Z"}
    group_leader_repo.update.return_value = updated_item
    payload = GroupLeaderUpdate(name="Ravi K")

    result = service.update_group_leader("gl-001", payload)

    call_fields = group_leader_repo.update.call_args[0][1]
    assert "name" in call_fields
    assert "bookstore_ids" not in call_fields
    assert result.name == "Ravi K"


def test_update_group_leader_raises_not_found(service, group_leader_repo):
    """update_group_leader should raise GroupLeaderNotFoundError when repo raises it."""
    group_leader_repo.update.side_effect = GroupLeaderNotFoundError("gl-999")
    payload = GroupLeaderUpdate(name="Ghost")

    with pytest.raises(GroupLeaderNotFoundError):
        service.update_group_leader("gl-999", payload)


def test_delete_group_leader_with_no_sellers_calls_repo_delete(service, group_leader_repo):
    """delete_group_leader should call repo.delete when seller count is 0."""
    group_leader_repo.count_active_sellers.return_value = 0

    service.delete_group_leader("gl-001")

    group_leader_repo.delete.assert_called_once_with("gl-001")


def test_delete_group_leader_raises_active_sellers_error(service, group_leader_repo):
    """delete_group_leader should raise ActiveSellersExistError when sellers are assigned."""
    group_leader_repo.count_active_sellers.return_value = 3

    with pytest.raises(ActiveSellersExistError):
        service.delete_group_leader("gl-001")

    group_leader_repo.delete.assert_not_called()


def test_delete_group_leader_raises_not_found(service, group_leader_repo):
    """delete_group_leader should propagate GroupLeaderNotFoundError from repo."""
    group_leader_repo.count_active_sellers.return_value = 0
    group_leader_repo.delete.side_effect = GroupLeaderNotFoundError("gl-999")

    with pytest.raises(GroupLeaderNotFoundError):
        service.delete_group_leader("gl-999")
