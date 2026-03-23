"""Unit tests for SaleService.

Verifies all business logic using mocked repository ABCs.
No DynamoDB, no HTTP, no moto required.
"""

from decimal import Decimal
from unittest.mock import ANY, MagicMock, patch

import pytest
from pydantic import ValidationError

from bookrover.exceptions.bad_request import InsufficientInventoryError
from bookrover.exceptions.conflict import SellerPendingReturnError
from bookrover.exceptions.not_found import BookNotFoundError, SaleNotFoundError, SellerNotFoundError
from bookrover.models.sale import SaleCreate, SaleItemCreate
from bookrover.services.sale_service import SaleService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sale_repo():
    """Mock AbstractSaleRepository."""
    return MagicMock()


@pytest.fixture
def inventory_repo():
    """Mock AbstractInventoryRepository."""
    return MagicMock()


@pytest.fixture
def seller_repo():
    """Mock AbstractSellerRepository."""
    return MagicMock()


@pytest.fixture
def service(sale_repo, inventory_repo, seller_repo):
    """SaleService wired with mock repositories."""
    return SaleService(
        sale_repository=sale_repo,
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
    "bookstore_id": "bs-001",
    "status": "active",
    "created_at": "2026-01-01T00:00:00Z",
}

BOOK_ITEM = {
    "book_id": "book-001",
    "book_name": "Thirukkural",
    "language": "Tamil",
    "current_count": Decimal("10"),
    "selling_price": Decimal("75.00"),
    "seller_id": "sel-001",
    "bookstore_id": "bs-001",
}

SALE_PAYLOAD = SaleCreate(
    buyer_first_name="Ravi",
    buyer_last_name="Kumar",
    buyer_country_code="+91",
    buyer_phone="9876543210",
    items=[SaleItemCreate(book_id="book-001", quantity_sold=2)],
)

SALE_RECORD = {
    "sale_id": "sale-001",
    "seller_id": "sel-001",
    "bookstore_id": "bs-001",
    "buyer_first_name": "Ravi",
    "buyer_last_name": "Kumar",
    "buyer_country_code": "+91",
    "buyer_phone": "9876543210",
    "sale_items": [
        {
            "book_id": "book-001",
            "book_name": "Thirukkural",
            "language": "Tamil",
            "quantity_sold": 2,
            "selling_price": 75.0,
            "subtotal": 150.0,
        }
    ],
    "total_books_sold": 2,
    "total_amount_collected": 150.0,
    "sale_date": "2026-01-01T00:00:00Z",
    "created_at": "2026-01-01T00:00:00Z",
}


# ---------------------------------------------------------------------------
# create_sale — success path
# ---------------------------------------------------------------------------


def test_create_sale_returns_response_for_valid_input(service, sale_repo, inventory_repo, seller_repo):
    """create_sale should return SaleResponse when all inputs are valid."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.get_by_id.return_value = BOOK_ITEM

    with patch("bookrover.services.sale_service.generate_id", return_value="sale-001"):
        result = service.create_sale("sel-001", SALE_PAYLOAD)

    assert result.sale_id == "sale-001"
    assert result.seller_id == "sel-001"
    assert result.total_books_sold == 2
    assert result.total_amount_collected == 150.0


def test_create_sale_snapshots_book_data_in_sale_items(service, sale_repo, inventory_repo, seller_repo):
    """create_sale must snapshot book_name, language, selling_price at sale time."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.get_by_id.return_value = BOOK_ITEM
    sale_repo.create.return_value = SALE_RECORD

    service.create_sale("sel-001", SALE_PAYLOAD)

    persisted = sale_repo.create.call_args[0][0]
    item = persisted["sale_items"][0]
    assert item["book_name"] == "Thirukkural"
    assert item["language"] == "Tamil"
    assert item["selling_price"] == 75.0


def test_create_sale_computes_totals_correctly(service, sale_repo, inventory_repo, seller_repo):
    """create_sale must compute total_books_sold and total_amount_collected."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.get_by_id.return_value = BOOK_ITEM
    sale_repo.create.return_value = SALE_RECORD

    service.create_sale("sel-001", SALE_PAYLOAD)

    persisted = sale_repo.create.call_args[0][0]
    assert persisted["total_books_sold"] == 2
    assert persisted["total_amount_collected"] == 150.0


def test_create_sale_decrements_inventory_after_sale(service, sale_repo, inventory_repo, seller_repo):
    """create_sale must call inventory_repo.decrement_count with the sold quantity."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.get_by_id.return_value = BOOK_ITEM
    sale_repo.create.return_value = SALE_RECORD

    service.create_sale("sel-001", SALE_PAYLOAD)

    inventory_repo.decrement_count.assert_called_once_with("book-001", 2, ANY)


def test_create_sale_persists_before_decrementing_inventory(service, sale_repo, inventory_repo, seller_repo):
    """create_sale must persist the sale record before decrementing inventory."""
    call_order = []
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.get_by_id.return_value = BOOK_ITEM
    sale_repo.create.side_effect = lambda r: call_order.append("create") or r
    inventory_repo.decrement_count.side_effect = lambda *a, **kw: call_order.append("update")

    service.create_sale("sel-001", SALE_PAYLOAD)

    assert call_order.index("create") < call_order.index("update")


def test_create_sale_uses_seller_bookstore_id(service, sale_repo, inventory_repo, seller_repo):
    """create_sale must derive bookstore_id from the seller record."""
    seller_repo.get_by_id.return_value = {**SELLER_ITEM, "bookstore_id": "bs-999"}
    inventory_repo.get_by_id.return_value = BOOK_ITEM
    sale_repo.create.return_value = SALE_RECORD

    service.create_sale("sel-001", SALE_PAYLOAD)

    persisted = sale_repo.create.call_args[0][0]
    assert persisted["bookstore_id"] == "bs-999"


# ---------------------------------------------------------------------------
# create_sale — error paths
# ---------------------------------------------------------------------------


def test_create_sale_raises_seller_not_found(service, seller_repo):
    """create_sale raises SellerNotFoundError when seller does not exist."""
    seller_repo.get_by_id.return_value = None

    with pytest.raises(SellerNotFoundError):
        service.create_sale("no-seller", SALE_PAYLOAD)


def test_create_sale_raises_seller_pending_return(service, seller_repo):
    """create_sale raises SellerPendingReturnError when seller status is pending_return."""
    seller_repo.get_by_id.return_value = {**SELLER_ITEM, "status": "pending_return"}

    with pytest.raises(SellerPendingReturnError):
        service.create_sale("sel-001", SALE_PAYLOAD)


def test_create_sale_raises_book_not_found(service, inventory_repo, seller_repo):
    """create_sale raises BookNotFoundError when a book_id does not exist."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.get_by_id.return_value = None

    with pytest.raises(BookNotFoundError):
        service.create_sale("sel-001", SALE_PAYLOAD)


def test_create_sale_raises_insufficient_inventory(service, inventory_repo, seller_repo):
    """create_sale raises InsufficientInventoryError when quantity_sold > current_count."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.get_by_id.return_value = {**BOOK_ITEM, "current_count": Decimal("1")}

    payload = SaleCreate(
        buyer_first_name="Ravi",
        buyer_last_name="Kumar",
        buyer_country_code="+91",
        buyer_phone="9876543210",
        items=[SaleItemCreate(book_id="book-001", quantity_sold=5)],
    )

    with pytest.raises(InsufficientInventoryError) as exc_info:
        service.create_sale("sel-001", payload)

    assert exc_info.value.book_id == "book-001"
    assert exc_info.value.requested == 5
    assert exc_info.value.available == 1


def test_create_sale_does_not_mutate_inventory_if_book_not_found(
    service, sale_repo, inventory_repo, seller_repo
):
    """create_sale must not create the sale or decrement inventory if validation fails."""
    seller_repo.get_by_id.return_value = SELLER_ITEM
    inventory_repo.get_by_id.return_value = None

    with pytest.raises(BookNotFoundError):
        service.create_sale("sel-001", SALE_PAYLOAD)

    sale_repo.create.assert_not_called()
    inventory_repo.decrement_count.assert_not_called()


# ---------------------------------------------------------------------------
# list_sales
# ---------------------------------------------------------------------------


def test_list_sales_returns_all_for_seller(service, sale_repo):
    """list_sales should return all SaleResponse objects for a seller."""
    sale_repo.list_by_seller.return_value = [SALE_RECORD]

    result = service.list_sales("sel-001")

    sale_repo.list_by_seller.assert_called_once_with("sel-001")
    assert len(result) == 1
    assert result[0].sale_id == "sale-001"


def test_list_sales_returns_empty_list_when_no_sales(service, sale_repo):
    """list_sales should return an empty list when no sales exist."""
    sale_repo.list_by_seller.return_value = []

    result = service.list_sales("sel-001")

    assert result == []


# ---------------------------------------------------------------------------
# get_sale
# ---------------------------------------------------------------------------


def test_get_sale_returns_response_for_valid_ids(service, sale_repo):
    """get_sale should return SaleResponse when sale exists and belongs to seller."""
    sale_repo.get_by_id.return_value = SALE_RECORD

    result = service.get_sale("sel-001", "sale-001")

    assert result.sale_id == "sale-001"
    assert result.seller_id == "sel-001"


def test_get_sale_raises_not_found_for_missing_sale(service, sale_repo):
    """get_sale raises SaleNotFoundError when sale_id does not exist."""
    sale_repo.get_by_id.return_value = None

    with pytest.raises(SaleNotFoundError):
        service.get_sale("sel-001", "no-sale")


def test_get_sale_raises_not_found_for_wrong_seller(service, sale_repo):
    """get_sale raises SaleNotFoundError when sale belongs to a different seller."""
    sale_repo.get_by_id.return_value = {**SALE_RECORD, "seller_id": "other-seller"}

    with pytest.raises(SaleNotFoundError):
        service.get_sale("sel-001", "sale-001")


# ---------------------------------------------------------------------------
# SaleCreate model validation
# ---------------------------------------------------------------------------


def test_sale_create_rejects_duplicate_book_ids():
    """SaleCreate must reject an items list that contains duplicate book_id values."""
    with pytest.raises(ValidationError):
        SaleCreate(
            buyer_first_name="Ravi",
            buyer_last_name="Kumar",
            buyer_country_code="+91",
            buyer_phone="9876543210",
            items=[
                SaleItemCreate(book_id="book-001", quantity_sold=2),
                SaleItemCreate(book_id="book-001", quantity_sold=3),
            ],
        )
