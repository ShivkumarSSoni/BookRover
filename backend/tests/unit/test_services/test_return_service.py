"""Unit tests for ReturnService.

Verifies all business logic using mocked repository ABCs.
No DynamoDB, no HTTP, no moto required.
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from bookrover.exceptions.not_found import BookStoreNotFoundError, SellerNotFoundError
from bookrover.services.return_service import ReturnService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seller_repo():
    """Mock AbstractSellerRepository."""
    return MagicMock()


@pytest.fixture
def bookstore_repo():
    """Mock AbstractBookstoreRepository."""
    return MagicMock()


@pytest.fixture
def inventory_repo():
    """Mock AbstractInventoryRepository."""
    return MagicMock()


@pytest.fixture
def sale_repo():
    """Mock AbstractSaleRepository."""
    return MagicMock()


@pytest.fixture
def return_repo():
    """Mock AbstractReturnRepository."""
    return MagicMock()


@pytest.fixture
def service(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo):
    """ReturnService wired with all mock repositories."""
    return ReturnService(
        seller_repository=seller_repo,
        bookstore_repository=bookstore_repo,
        inventory_repository=inventory_repo,
        sale_repository=sale_repo,
        return_repository=return_repo,
    )


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

SELLER_ID = "seller-001"
BOOKSTORE_ID = "bs-001"

SELLER_ITEM = {
    "seller_id": SELLER_ID,
    "first_name": "Anand",
    "last_name": "Raj",
    "email": "anand@gmail.com",
    "bookstore_id": BOOKSTORE_ID,
    "group_leader_id": "gl-001",
    "status": "active",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

BOOKSTORE_ITEM = {
    "bookstore_id": BOOKSTORE_ID,
    "store_name": "Sri Lakshmi Books",
    "owner_name": "Lakshmi Devi",
    "address": "12 MG Road, Chennai",
    "phone_number": "+914423456789",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

BOOK_A = {
    "book_id": "book-001",
    "seller_id": SELLER_ID,
    "bookstore_id": BOOKSTORE_ID,
    "book_name": "Thirukkural",
    "language": "Tamil",
    "initial_count": Decimal("10"),
    "current_count": Decimal("8"),
    "cost_per_book": Decimal("50.00"),
    "selling_price": Decimal("75.00"),
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

BOOK_B = {
    "book_id": "book-002",
    "seller_id": SELLER_ID,
    "bookstore_id": BOOKSTORE_ID,
    "book_name": "Bible Stories",
    "language": "English",
    "initial_count": Decimal("5"),
    "current_count": Decimal("3"),
    "cost_per_book": Decimal("80.00"),
    "selling_price": Decimal("120.00"),
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

SALE_ITEM = {
    "sale_id": "sale-001",
    "seller_id": SELLER_ID,
    "total_amount_collected": Decimal("225.00"),
    "total_books_sold": Decimal("3"),
}


def _setup_defaults(
    seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """Seed all mocks with default happy-path return values."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    bookstore_repo.get_by_id.return_value = BOOKSTORE_ITEM
    inventory_repo.list_by_seller.return_value = [BOOK_A, BOOK_B]
    sale_repo.list_by_seller.return_value = [SALE_ITEM]
    return_repo.create.side_effect = lambda item: item


# ---------------------------------------------------------------------------
# get_return_summary
# ---------------------------------------------------------------------------


def test_get_return_summary_returns_bookstore_info(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary includes full bookstore contact details."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    result = service.get_return_summary(SELLER_ID)

    assert result.bookstore.store_name == "Sri Lakshmi Books"
    assert result.bookstore.owner_name == "Lakshmi Devi"
    assert result.bookstore.address == "12 MG Road, Chennai"
    assert result.bookstore.phone_number == "+914423456789"


def test_get_return_summary_lists_only_books_with_stock(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary includes only books where current_count > 0."""
    sold_out_book = {**BOOK_A, "book_id": "book-sold", "current_count": Decimal("0")}
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)
    inventory_repo.list_by_seller.return_value = [BOOK_A, BOOK_B, sold_out_book]

    result = service.get_return_summary(SELLER_ID)

    book_ids = [b.book_id for b in result.books_to_return]
    assert "book-001" in book_ids
    assert "book-002" in book_ids
    assert "book-sold" not in book_ids


def test_get_return_summary_computes_total_books_and_cost(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary correctly computes total_books_to_return and total cost."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    result = service.get_return_summary(SELLER_ID)

    # BOOK_A: 8 × 50 = 400, BOOK_B: 3 × 80 = 240 → total 11 books, ₹640
    assert result.total_books_to_return == 11
    assert result.total_cost_of_unsold_books == pytest.approx(640.0)


def test_get_return_summary_computes_total_money_from_sales(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary sums total_amount_collected from all sales."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)
    sale_repo.list_by_seller.return_value = [
        {**SALE_ITEM, "total_amount_collected": Decimal("225.00")},
        {"sale_id": "sale-002", "total_amount_collected": Decimal("100.00")},
    ]

    result = service.get_return_summary(SELLER_ID)

    assert result.total_money_collected_from_sales == pytest.approx(325.0)


def test_get_return_summary_returns_zero_money_when_no_sales(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary reports zero money collected when there are no sales."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)
    sale_repo.list_by_seller.return_value = []

    result = service.get_return_summary(SELLER_ID)

    assert result.total_money_collected_from_sales == 0.0


def test_get_return_summary_returns_empty_books_when_all_sold(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary has empty books_to_return when all books are sold out."""
    sold_out = {**BOOK_A, "current_count": Decimal("0")}
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)
    inventory_repo.list_by_seller.return_value = [sold_out]

    result = service.get_return_summary(SELLER_ID)

    assert result.books_to_return == []
    assert result.total_books_to_return == 0
    assert result.total_cost_of_unsold_books == 0.0


def test_get_return_summary_raises_seller_not_found(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary raises SellerNotFoundError when seller does not exist."""
    seller_repo.get_by_id.return_value = None

    with pytest.raises(SellerNotFoundError):
        service.get_return_summary("unknown-seller")


def test_get_return_summary_raises_bookstore_not_found(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary raises BookStoreNotFoundError when bookstore cannot be found."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)
    bookstore_repo.get_by_id.return_value = None

    with pytest.raises(BookStoreNotFoundError):
        service.get_return_summary(SELLER_ID)


def test_get_return_summary_includes_per_book_total_cost(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """get_return_summary computes total_cost per book correctly."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    result = service.get_return_summary(SELLER_ID)

    book_a = next(b for b in result.books_to_return if b.book_id == "book-001")
    assert book_a.quantity_to_return == 8
    assert book_a.cost_per_book == pytest.approx(50.0)
    assert book_a.total_cost == pytest.approx(400.0)


# ---------------------------------------------------------------------------
# submit_return
# ---------------------------------------------------------------------------


def test_submit_return_persists_return_record(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return calls return_repo.create with a properly constructed record."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    service.submit_return(SELLER_ID, notes=None)

    return_repo.create.assert_called_once()
    record = return_repo.create.call_args[0][0]
    assert record["seller_id"] == SELLER_ID
    assert record["bookstore_id"] == BOOKSTORE_ID
    assert record["status"] == "completed"
    assert len(record["return_items"]) == 2


def test_submit_return_computes_total_books_returned(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return sums quantities across all return items."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    result = service.submit_return(SELLER_ID, notes=None)

    # BOOK_A: 8 + BOOK_B: 3 = 11
    assert result.total_books_returned == 11


def test_submit_return_computes_total_money_returned(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return total_money_returned is sum of all sale totals."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    result = service.submit_return(SELLER_ID, notes=None)

    assert result.total_money_returned == pytest.approx(225.0)


def test_submit_return_deletes_all_inventory_books(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return calls inventory_repo.delete for every book in inventory."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    service.submit_return(SELLER_ID, notes=None)

    assert inventory_repo.delete.call_count == 2
    deleted_ids = {c.args[0] for c in inventory_repo.delete.call_args_list}
    assert "book-001" in deleted_ids
    assert "book-002" in deleted_ids


def test_submit_return_resets_seller_status_to_active(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return updates seller status to 'active'."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    service.submit_return(SELLER_ID, notes=None)

    seller_repo.update.assert_called_once()
    update_args = seller_repo.update.call_args[0]
    assert update_args[0] == SELLER_ID
    assert update_args[1]["status"] == "active"


def test_submit_return_only_returns_books_with_stock(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return only includes books with current_count > 0 in the record."""
    sold_out = {**BOOK_A, "book_id": "book-sold", "current_count": Decimal("0")}
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)
    inventory_repo.list_by_seller.return_value = [BOOK_A, BOOK_B, sold_out]

    service.submit_return(SELLER_ID, notes=None)

    record = return_repo.create.call_args[0][0]
    returned_book_ids = [item["book_id"] for item in record["return_items"]]
    assert "book-sold" not in returned_book_ids
    # But sold_out book is still deleted from inventory
    deleted_ids = {c.args[0] for c in inventory_repo.delete.call_args_list}
    assert "book-sold" in deleted_ids


def test_submit_return_raises_seller_not_found(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return raises SellerNotFoundError when seller does not exist."""
    seller_repo.get_by_id.return_value = None

    with pytest.raises(SellerNotFoundError):
        service.submit_return("unknown-seller", notes=None)


def test_submit_return_stores_notes_when_provided(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return includes notes in the persisted record when provided."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    service.submit_return(SELLER_ID, notes="All books in good condition")

    record = return_repo.create.call_args[0][0]
    assert record.get("notes") == "All books in good condition"


def test_submit_return_response_contains_correct_fields(
    service, seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo
):
    """submit_return returns a ReturnResponse with all expected fields populated."""
    _setup_defaults(seller_repo, bookstore_repo, inventory_repo, sale_repo, return_repo)

    result = service.submit_return(SELLER_ID, notes=None)

    assert result.seller_id == SELLER_ID
    assert result.bookstore_id == BOOKSTORE_ID
    assert result.status == "completed"
    assert result.return_id is not None
    assert result.return_date is not None
    assert len(result.return_items) == 2
