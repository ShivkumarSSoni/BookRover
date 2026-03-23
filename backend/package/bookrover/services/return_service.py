"""Business logic layer for the Return feature.

Handles:
  - Building the return summary (books still in hand + money collected from sales).
  - Submitting a return: persisting the return record, deleting all inventory books,
    and resetting the seller status to 'active'.

Has zero knowledge of DynamoDB, HTTP, or Lambda — all external concerns
are injected through repository abstractions.
"""

import logging
from decimal import Decimal
from typing import Optional

from bookrover.exceptions.not_found import BookStoreNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_bookstore_repository import AbstractBookstoreRepository
from bookrover.interfaces.abstract_inventory_repository import AbstractInventoryRepository
from bookrover.interfaces.abstract_return_repository import AbstractReturnRepository
from bookrover.interfaces.abstract_return_service import AbstractReturnService
from bookrover.interfaces.abstract_sale_repository import AbstractSaleRepository
from bookrover.interfaces.abstract_seller_repository import AbstractSellerRepository
from bookrover.models.return_models import (
    ReturnItemResponse,
    ReturnResponse,
    ReturnSummaryBook,
    ReturnSummaryBookstoreInfo,
    ReturnSummaryResponse,
)
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso

logger = logging.getLogger(__name__)

_SELLER_STATUS_ACTIVE = "active"
_RETURN_STATUS_COMPLETED = "completed"


class ReturnService(AbstractReturnService):
    """Concrete implementation of AbstractReturnService.

    Orchestrates inventory reads, sale aggregation, return record creation,
    inventory deletion, and seller status reset to deliver the return feature.

    Args:
        seller_repository: Injected AbstractSellerRepository.
        bookstore_repository: Injected AbstractBookstoreRepository.
        inventory_repository: Injected AbstractInventoryRepository.
        sale_repository: Injected AbstractSaleRepository.
        return_repository: Injected AbstractReturnRepository.
    """

    def __init__(
        self,
        seller_repository: AbstractSellerRepository,
        bookstore_repository: AbstractBookstoreRepository,
        inventory_repository: AbstractInventoryRepository,
        sale_repository: AbstractSaleRepository,
        return_repository: AbstractReturnRepository,
    ) -> None:
        self._seller_repository = seller_repository
        self._bookstore_repository = bookstore_repository
        self._inventory_repository = inventory_repository
        self._sale_repository = sale_repository
        self._return_repository = return_repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_return_summary(self, seller_id: str) -> ReturnSummaryResponse:
        """Build the return summary for a seller.

        Fetches the seller's bookstore, all inventory books with current_count > 0,
        and the total money collected from all sales.

        Args:
            seller_id: UUID of the seller.

        Returns:
            ReturnSummaryResponse with bookstore info, books to return, and totals.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
            BookStoreNotFoundError: If the seller's bookstore cannot be found.
        """
        seller = self._seller_repository.get_by_id(seller_id)
        if seller is None:
            raise SellerNotFoundError(seller_id)

        bookstore = self._bookstore_repository.get_by_id(seller["bookstore_id"])
        if bookstore is None:
            raise BookStoreNotFoundError(seller["bookstore_id"])

        all_books = self._inventory_repository.list_by_seller(seller_id)
        books_with_stock = [b for b in all_books if int(b.get("current_count", 0)) > 0]

        summary_books = [self._to_summary_book(b) for b in books_with_stock]

        total_books = sum(b.quantity_to_return for b in summary_books)
        total_cost = sum(b.total_cost for b in summary_books)

        all_sales = self._sale_repository.list_by_seller(seller_id)
        total_money = sum(
            float(s.get("total_amount_collected", 0)) for s in all_sales
        )

        return ReturnSummaryResponse(
            seller_id=seller_id,
            bookstore=ReturnSummaryBookstoreInfo(
                bookstore_id=bookstore["bookstore_id"],
                store_name=bookstore["store_name"],
                owner_name=bookstore["owner_name"],
                address=bookstore["address"],
                phone_number=bookstore["phone_number"],
            ),
            books_to_return=summary_books,
            total_books_to_return=total_books,
            total_cost_of_unsold_books=total_cost,
            total_money_collected_from_sales=total_money,
        )

    def submit_return(self, seller_id: str, notes: Optional[str]) -> ReturnResponse:
        """Submit a return: persist the record, clear inventory, reset seller status.

        Side effects (in order):
          1. Persist the Return record with all current inventory as return_items.
          2. Delete every inventory book for this seller.
          3. Reset the seller's status to 'active'.

        Args:
            seller_id: UUID of the seller submitting the return.
            notes: Optional freeform notes about the return.

        Returns:
            ReturnResponse representing the completed return record.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
        """
        seller = self._seller_repository.get_by_id(seller_id)
        if seller is None:
            raise SellerNotFoundError(seller_id)

        all_books = self._inventory_repository.list_by_seller(seller_id)
        books_with_stock = [b for b in all_books if int(b.get("current_count", 0)) > 0]

        return_items = [self._to_return_item_dict(b) for b in books_with_stock]

        all_sales = self._sale_repository.list_by_seller(seller_id)
        total_money = sum(
            float(s.get("total_amount_collected", 0)) for s in all_sales
        )

        now = utc_now_iso()
        return_record = {
            "return_id": generate_id(),
            "seller_id": seller_id,
            "bookstore_id": seller["bookstore_id"],
            "return_items": return_items,
            "total_books_returned": sum(item["quantity_returned"] for item in return_items),
            "total_money_returned": Decimal(str(round(total_money, 2))),
            "status": _RETURN_STATUS_COMPLETED,
            "return_date": now,
            "created_at": now,
        }
        if notes:
            return_record["notes"] = notes

        persisted = self._return_repository.create(return_record)

        for book in all_books:
            self._inventory_repository.delete(book["book_id"])

        self._seller_repository.update(seller_id, {
            "status": _SELLER_STATUS_ACTIVE,
            "updated_at": now,
        })

        logger.info(
            "Return submitted",
            extra={
                "seller_id": seller_id,
                "return_id": persisted["return_id"],
                "total_books": persisted["total_books_returned"],
            },
        )

        return self._to_return_response(persisted)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_summary_book(book: dict) -> ReturnSummaryBook:
        """Convert an inventory book dict to a ReturnSummaryBook DTO.

        Args:
            book: Raw inventory book dict from the repository.

        Returns:
            ReturnSummaryBook DTO with computed total_cost.
        """
        qty = int(book["current_count"])
        cost = float(book["cost_per_book"])
        return ReturnSummaryBook(
            book_id=book["book_id"],
            book_name=book["book_name"],
            language=book["language"],
            quantity_to_return=qty,
            cost_per_book=cost,
            total_cost=round(qty * cost, 2),
        )

    @staticmethod
    def _to_return_item_dict(book: dict) -> dict:
        """Convert an inventory book dict to a return_items element for DynamoDB.

        Args:
            book: Raw inventory book dict from the repository.

        Returns:
            Dict with return item fields (using Decimal for DynamoDB compatibility).
        """
        qty = int(book["current_count"])
        cost = Decimal(str(book["cost_per_book"]))
        return {
            "book_id": book["book_id"],
            "book_name": book["book_name"],
            "language": book["language"],
            "quantity_returned": qty,
            "cost_per_book": cost,
            "total_cost": Decimal(str(round(qty * float(cost), 2))),
        }

    @staticmethod
    def _to_return_response(record: dict) -> ReturnResponse:
        """Convert a persisted return record dict to a ReturnResponse DTO.

        Args:
            record: Raw Return dict as stored/retrieved from the repository.

        Returns:
            ReturnResponse Pydantic model.
        """
        items = [
            ReturnItemResponse(
                book_id=item["book_id"],
                book_name=item["book_name"],
                language=item["language"],
                quantity_returned=int(item["quantity_returned"]),
                cost_per_book=float(item["cost_per_book"]),
                total_cost=float(item["total_cost"]),
            )
            for item in record.get("return_items", [])
        ]
        return ReturnResponse(
            return_id=record["return_id"],
            seller_id=record["seller_id"],
            bookstore_id=record["bookstore_id"],
            return_items=items,
            total_books_returned=int(record["total_books_returned"]),
            total_money_returned=float(record["total_money_returned"]),
            status=record["status"],
            return_date=record["return_date"],
        )
