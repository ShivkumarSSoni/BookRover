"""Business logic layer for the Sales feature.

Owns all business rules for recording a sale and decrementing inventory.
Has zero knowledge of DynamoDB, HTTP, or Lambda — all external concerns
are injected through repository abstractions.
"""

import logging
from decimal import Decimal
from typing import Dict, List

from bookrover.exceptions.bad_request import InsufficientInventoryError
from bookrover.exceptions.conflict import SellerPendingReturnError
from bookrover.exceptions.not_found import BookNotFoundError, SaleNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_inventory_repository import AbstractInventoryRepository
from bookrover.interfaces.abstract_sale_repository import AbstractSaleRepository
from bookrover.interfaces.abstract_sale_service import AbstractSaleService
from bookrover.interfaces.abstract_seller_repository import AbstractSellerRepository
from bookrover.models.sale import SaleCreate, SaleItemResponse, SaleResponse
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso

logger = logging.getLogger(__name__)


class SaleService(AbstractSaleService):
    """Concrete implementation of AbstractSaleService.

    Orchestrates sale creation by validating seller and inventory state,
    snapshotting book data, persisting the sale, and decrementing inventory.

    Args:
        sale_repository: Injected AbstractSaleRepository implementation.
        inventory_repository: Injected AbstractInventoryRepository — used to
            validate stock and decrement current_count after each sale.
        seller_repository: Injected AbstractSellerRepository — used to verify
            seller existence and status before allowing a sale.
    """

    def __init__(
        self,
        sale_repository: AbstractSaleRepository,
        inventory_repository: AbstractInventoryRepository,
        seller_repository: AbstractSellerRepository,
    ) -> None:
        self._sale_repository = sale_repository
        self._inventory_repository = inventory_repository
        self._seller_repository = seller_repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_sale(self, seller_id: str, payload: SaleCreate) -> SaleResponse:
        """Record a new sale and decrement current_count for each sold book.

        All books are validated upfront before any mutation to preserve
        consistency — if any book fails validation the sale is not written.

        Args:
            seller_id: UUID of the seller recording the sale.
            payload: Validated SaleCreate DTO (buyer details + items).

        Returns:
            SaleResponse for the created sale.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
            SellerPendingReturnError: If seller status is 'pending_return'.
            BookNotFoundError: If any book_id in items does not exist.
            InsufficientInventoryError: If quantity_sold exceeds current_count.
        """
        seller = self._seller_repository.get_by_id(seller_id)
        if seller is None:
            raise SellerNotFoundError(seller_id)
        if seller.get("status") == "pending_return":
            raise SellerPendingReturnError(seller_id)

        # Resolve and validate all items upfront — no mutation yet.
        resolved_items: List[tuple] = []
        for item in payload.items:
            book = self._inventory_repository.get_by_id(item.book_id)
            if book is None:
                raise BookNotFoundError(item.book_id)
            current_count = int(book["current_count"])
            if item.quantity_sold > current_count:
                raise InsufficientInventoryError(item.book_id, item.quantity_sold, current_count)
            resolved_items.append((item, book))

        # Build sale record with snapshotted book data.
        now = utc_now_iso()
        sale_items_raw: List[Dict] = []
        total_books_sold = 0
        total_amount_collected = Decimal("0")

        for item, book in resolved_items:
            selling_price = Decimal(str(book["selling_price"]))
            subtotal = selling_price * Decimal(str(item.quantity_sold))
            total_books_sold += item.quantity_sold
            total_amount_collected += subtotal
            sale_items_raw.append({
                "book_id": item.book_id,
                "book_name": book["book_name"],
                "language": book["language"],
                "quantity_sold": item.quantity_sold,
                "selling_price": selling_price,
                "subtotal": subtotal,
            })

        sale_record = {
            "sale_id": generate_id(),
            "seller_id": seller_id,
            "bookstore_id": seller["bookstore_id"],
            "buyer_first_name": payload.buyer_first_name,
            "buyer_last_name": payload.buyer_last_name,
            "buyer_country_code": payload.buyer_country_code,
            "buyer_phone": payload.buyer_phone,
            "sale_items": sale_items_raw,
            "total_books_sold": total_books_sold,
            "total_amount_collected": total_amount_collected,
            "sale_date": now,
            "created_at": now,
        }
        self._sale_repository.create(sale_record)

        # Decrement inventory counts after the sale is persisted.
        for item, book in resolved_items:
            new_count = int(book["current_count"]) - item.quantity_sold
            self._inventory_repository.update(
                item.book_id,
                {"current_count": new_count, "updated_at": now},
            )
            logger.info(
                "Inventory decremented",
                extra={"book_id": item.book_id, "sold": item.quantity_sold, "remaining": new_count},
            )

        return self._to_sale_response(sale_record)

    def list_sales(self, seller_id: str) -> List[SaleResponse]:
        """Return all sales for a seller.

        Args:
            seller_id: UUID of the seller.

        Returns:
            List of SaleResponse objects, may be empty.
        """
        items = self._sale_repository.list_by_seller(seller_id)
        return [self._to_sale_response(item) for item in items]

    def get_sale(self, seller_id: str, sale_id: str) -> SaleResponse:
        """Return a single sale by ID, scoped to the seller.

        Args:
            seller_id: UUID of the seller (ownership check).
            sale_id: UUID of the sale to retrieve.

        Returns:
            SaleResponse for the matching sale.

        Raises:
            SaleNotFoundError: If sale is not found or belongs to a different seller.
        """
        item = self._sale_repository.get_by_id(sale_id)
        if item is None or item.get("seller_id") != seller_id:
            raise SaleNotFoundError(sale_id)
        return self._to_sale_response(item)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_sale_response(item: Dict) -> SaleResponse:
        """Convert a raw DynamoDB Sale dict to a SaleResponse DTO.

        Explicit int/float conversions guard against DynamoDB returning
        Decimal where Pydantic expects a native Python numeric type.

        Args:
            item: Raw Sale dict from DynamoDB (or freshly built dict).

        Returns:
            SaleResponse DTO.
        """
        sale_items = [
            SaleItemResponse(
                book_id=si["book_id"],
                book_name=si["book_name"],
                language=si["language"],
                quantity_sold=int(si["quantity_sold"]),
                selling_price=float(si["selling_price"]),
                subtotal=float(si["subtotal"]),
            )
            for si in item.get("sale_items", [])
        ]
        return SaleResponse(
            sale_id=item["sale_id"],
            seller_id=item["seller_id"],
            bookstore_id=item["bookstore_id"],
            buyer_first_name=item["buyer_first_name"],
            buyer_last_name=item["buyer_last_name"],
            buyer_country_code=item["buyer_country_code"],
            buyer_phone=item["buyer_phone"],
            sale_items=sale_items,
            total_books_sold=int(item["total_books_sold"]),
            total_amount_collected=float(item["total_amount_collected"]),
            sale_date=item["sale_date"],
            created_at=item["created_at"],
        )
