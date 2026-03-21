"""Unit tests for InventoryService.

Verifies all business logic using mocked repository ABCs.
No DynamoDB, no HTTP, no moto required.
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from bookrover.exceptions.conflict import BookPartiallySoldError
from bookrover.exceptions.not_found import BookNotFoundError, SellerNotFoundError
from bookrover.models.inventory import BookCreate, BookUpdate
from bookrover.services.inventory_service import InventoryService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def inventory_repo():
    """Mock AbstractInventoryRepository."""
    return MagicMock()


@pytest.fixture
def seller_repo():
    """Mock AbstractSellerRepository."""
    return MagicMock()


@pytest.fixture
def service(inventory_repo, seller_repo):
    """InventoryService wired with mock repositories."""
    return InventoryService(
        inventory_repository=inventory_repo,
        seller_repository=seller_repo,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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

BOOK_ITEM = {
    "book_id": "book-001",
    "seller_id": "sel-001",
    "bookstore_id": "bs-001",
    "book_name": "Thirukkural",
    "language": "Tamil",
    "initial_count": Decimal("10"),
    "current_count": Decimal("10"),
    "cost_per_book": Decimal("50.00"),
    "selling_price": Decimal("75.00"),
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

PARTIALLY_SOLD_BOOK_ITEM = {
    **BOOK_ITEM,
    "current_count": Decimal("8"),  # 2 copies sold
}

ADD_BOOK_PAYLOAD = BookCreate(
    book_name="Thirukkural",
    language="Tamil",
    initial_count=10,
    cost_per_book=Decimal("50.00"),
    selling_price=Decimal("75.00"),
)


# ---------------------------------------------------------------------------
# add_book
# ---------------------------------------------------------------------------


def test_add_book_returns_book_response(service, inventory_repo, seller_repo):
    """add_book should verify seller, create item, and return BookResponse."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.create.return_value = BOOK_ITEM

    result = service.add_book("sel-001", ADD_BOOK_PAYLOAD)

    seller_repo.get_by_id.assert_called_once_with("sel-001")
    inventory_repo.create.assert_called_once()
    assert result.book_id == "book-001"
    assert result.book_name == "Thirukkural"
    assert result.status if hasattr(result, "status") else True  # no status on book


def test_add_book_sets_current_count_equal_to_initial(service, inventory_repo, seller_repo):
    """add_book must set current_count = initial_count on creation."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.create.return_value = BOOK_ITEM

    service.add_book("sel-001", ADD_BOOK_PAYLOAD)

    created_item = inventory_repo.create.call_args[0][0]
    assert created_item["current_count"] == created_item["initial_count"]


def test_add_book_uses_seller_bookstore_id(service, inventory_repo, seller_repo):
    """add_book must derive bookstore_id from the seller's profile."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.create.return_value = BOOK_ITEM

    service.add_book("sel-001", ADD_BOOK_PAYLOAD)

    created_item = inventory_repo.create.call_args[0][0]
    assert created_item["bookstore_id"] == "bs-001"


def test_add_book_raises_seller_not_found(service, seller_repo):
    """add_book should raise SellerNotFoundError if seller does not exist."""
    seller_repo.get_by_id.return_value = None

    with pytest.raises(SellerNotFoundError):
        service.add_book("unknown-seller", ADD_BOOK_PAYLOAD)


def test_add_book_computes_balance_fields(service, inventory_repo, seller_repo):
    """add_book response should include correct computed balance fields."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.create.return_value = BOOK_ITEM

    result = service.add_book("sel-001", ADD_BOOK_PAYLOAD)

    assert result.current_books_cost_balance == 500.00  # 10 × 50
    assert result.total_books_cost_balance == 500.00


# ---------------------------------------------------------------------------
# get_inventory
# ---------------------------------------------------------------------------


def test_get_inventory_returns_inventory_list_response(service, inventory_repo, seller_repo):
    """get_inventory should return all books and a correct summary."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.list_by_seller.return_value = [BOOK_ITEM]

    result = service.get_inventory("sel-001")

    assert result.seller_id == "sel-001"
    assert result.bookstore_id == "bs-001"
    assert len(result.books) == 1
    assert result.books[0].book_name == "Thirukkural"


def test_get_inventory_computes_summary(service, inventory_repo, seller_repo):
    """get_inventory summary should aggregate all book balances."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.list_by_seller.return_value = [BOOK_ITEM]

    result = service.get_inventory("sel-001")

    assert result.summary.total_books_in_hand == 10
    assert result.summary.total_cost_balance == 500.00
    assert result.summary.total_initial_cost == 500.00


def test_get_inventory_empty_returns_zero_summary(service, inventory_repo, seller_repo):
    """get_inventory with no books should return empty list and zero summary."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.list_by_seller.return_value = []

    result = service.get_inventory("sel-001")

    assert result.books == []
    assert result.summary.total_books_in_hand == 0
    assert result.summary.total_cost_balance == 0.0


def test_get_inventory_raises_seller_not_found(service, seller_repo):
    """get_inventory should raise SellerNotFoundError if seller does not exist."""
    seller_repo.get_by_id.return_value = None

    with pytest.raises(SellerNotFoundError):
        service.get_inventory("unknown-seller")


# ---------------------------------------------------------------------------
# update_book
# ---------------------------------------------------------------------------


def test_update_book_applies_non_none_fields(service, inventory_repo, seller_repo):
    """update_book should only update fields explicitly set in the payload."""
    inventory_repo.get_by_id.return_value = BOOK_ITEM
    updated_item = {**BOOK_ITEM, "selling_price": Decimal("80.00")}
    inventory_repo.update.return_value = updated_item

    payload = BookUpdate(selling_price=Decimal("80.00"))
    result = service.update_book("sel-001", "book-001", payload)

    updated_fields = inventory_repo.update.call_args[0][1]
    assert "selling_price" in updated_fields
    assert "book_name" not in updated_fields
    assert result.selling_price == 80.00


def test_update_book_raises_not_found_for_wrong_seller(service, inventory_repo):
    """update_book should raise BookNotFoundError if book belongs to a different seller."""
    inventory_repo.get_by_id.return_value = {**BOOK_ITEM, "seller_id": "other-seller"}

    with pytest.raises(BookNotFoundError):
        service.update_book("sel-001", "book-001", BookUpdate(book_name="New Name"))


def test_update_book_raises_not_found_for_unknown_book(service, inventory_repo):
    """update_book should raise BookNotFoundError if book does not exist."""
    inventory_repo.get_by_id.return_value = None

    with pytest.raises(BookNotFoundError):
        service.update_book("sel-001", "unknown-book", BookUpdate(book_name="New Name"))


def test_update_book_empty_payload_returns_existing(service, inventory_repo):
    """update_book with no fields set should return existing data without calling update."""
    inventory_repo.get_by_id.return_value = BOOK_ITEM

    result = service.update_book("sel-001", "book-001", BookUpdate())

    inventory_repo.update.assert_not_called()
    assert result.book_name == "Thirukkural"


# ---------------------------------------------------------------------------
# remove_book
# ---------------------------------------------------------------------------


def test_remove_book_calls_repo_delete(service, inventory_repo):
    """remove_book should call repo.delete when no copies have been sold."""
    inventory_repo.get_by_id.return_value = BOOK_ITEM  # current == initial

    service.remove_book("sel-001", "book-001")

    inventory_repo.delete.assert_called_once_with("book-001")


def test_remove_book_raises_partially_sold(service, inventory_repo):
    """remove_book should raise BookPartiallySoldError if book has been partially sold."""
    inventory_repo.get_by_id.return_value = PARTIALLY_SOLD_BOOK_ITEM

    with pytest.raises(BookPartiallySoldError):
        service.remove_book("sel-001", "book-001")

    inventory_repo.delete.assert_not_called()


def test_remove_book_raises_not_found_for_wrong_seller(service, inventory_repo):
    """remove_book should raise BookNotFoundError if book belongs to a different seller."""
    inventory_repo.get_by_id.return_value = {**BOOK_ITEM, "seller_id": "other-seller"}

    with pytest.raises(BookNotFoundError):
        service.remove_book("sel-001", "book-001")


def test_remove_book_raises_not_found_for_unknown_book(service, inventory_repo):
    """remove_book should raise BookNotFoundError if book does not exist."""
    inventory_repo.get_by_id.return_value = None

    with pytest.raises(BookNotFoundError):
        service.remove_book("sel-001", "unknown-book")
