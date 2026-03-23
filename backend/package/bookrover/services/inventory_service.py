"""Business logic layer for the Inventory feature.

Owns all business rules for adding, listing, updating, and removing books
from a seller's inventory. Has zero knowledge of DynamoDB, HTTP, or Lambda —
all external concerns are injected through repository abstractions.
"""

import logging
from typing import Dict

from bookrover.exceptions.conflict import BookPartiallySoldError
from bookrover.exceptions.not_found import BookNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_inventory_repository import AbstractInventoryRepository
from bookrover.interfaces.abstract_inventory_service import AbstractInventoryService
from bookrover.interfaces.abstract_seller_repository import AbstractSellerRepository
from bookrover.models.inventory import (
    BookCreate,
    BookResponse,
    BookUpdate,
    InventoryListResponse,
    InventorySummary,
)
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso

logger = logging.getLogger(__name__)


class InventoryService(AbstractInventoryService):
    """Concrete implementation of AbstractInventoryService.

    Orchestrates inventory operations by delegating all persistence calls
    to the injected repository abstractions.

    Args:
        inventory_repository: Injected AbstractInventoryRepository implementation.
        seller_repository: Injected AbstractSellerRepository — used to verify
            seller existence and retrieve bookstore_id on book creation.
    """

    def __init__(
        self,
        inventory_repository: AbstractInventoryRepository,
        seller_repository: AbstractSellerRepository,
    ) -> None:
        self._inventory_repository = inventory_repository
        self._seller_repository = seller_repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_book(self, seller_id: str, payload: BookCreate) -> BookResponse:
        """Add a new book to a seller's inventory.

        The book's bookstore_id is derived from the seller's profile.
        current_count is set equal to initial_count on creation.

        Args:
            seller_id: UUID of the seller adding the book.
            payload: Validated BookCreate DTO.

        Returns:
            BookResponse for the newly created book.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
        """
        seller = self._seller_repository.get_by_id(seller_id)
        if seller is None:
            raise SellerNotFoundError(seller_id)

        now = utc_now_iso()
        item = {
            "book_id": generate_id(),
            "seller_id": seller_id,
            "bookstore_id": seller["bookstore_id"],
            "book_name": payload.book_name,
            "language": payload.language,
            "initial_count": payload.initial_count,
            "current_count": payload.initial_count,
            "cost_per_book": payload.cost_per_book,
            "selling_price": payload.selling_price,
            "created_at": now,
            "updated_at": now,
        }
        persisted = self._inventory_repository.create(item)
        logger.info("Book added to inventory", extra={"book_id": persisted["book_id"], "seller_id": seller_id})
        return self._to_book_response(persisted)

    def get_inventory(self, seller_id: str) -> InventoryListResponse:
        """Return the full inventory for a seller with aggregate summary.

        Args:
            seller_id: UUID of the seller.

        Returns:
            InventoryListResponse containing all books and computed summary.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
        """
        seller = self._seller_repository.get_by_id(seller_id)
        if seller is None:
            raise SellerNotFoundError(seller_id)

        items = self._inventory_repository.list_by_seller(seller_id)
        books = [self._to_book_response(item) for item in items]

        total_books_in_hand = sum(b.current_count for b in books)
        total_cost_balance = round(sum(b.current_books_cost_balance for b in books), 2)
        total_initial_cost = round(sum(b.total_books_cost_balance for b in books), 2)

        logger.info("Inventory listed", extra={"seller_id": seller_id, "book_count": len(books)})
        return InventoryListResponse(
            seller_id=seller_id,
            bookstore_id=seller["bookstore_id"],
            books=books,
            summary=InventorySummary(
                total_books_in_hand=total_books_in_hand,
                total_cost_balance=total_cost_balance,
                total_initial_cost=total_initial_cost,
            ),
        )

    def update_book(self, seller_id: str, book_id: str, payload: BookUpdate) -> BookResponse:
        """Apply a partial update to a book in a seller's inventory.

        Only fields explicitly set in the payload (non-None) are updated.
        updated_at is always refreshed.

        Args:
            seller_id: UUID of the seller (for ownership verification).
            book_id: UUID of the book to update.
            payload: Validated BookUpdate DTO.

        Returns:
            Updated BookResponse with recomputed balance fields.

        Raises:
            BookNotFoundError: If book does not exist or does not belong to seller.
        """
        existing = self._inventory_repository.get_by_id(book_id)
        if existing is None or existing.get("seller_id") != seller_id:
            raise BookNotFoundError(book_id)

        fields: Dict = {
            k: v for k, v in payload.model_dump().items() if v is not None
        }
        if not fields:
            return self._to_book_response(existing)

        fields["updated_at"] = utc_now_iso()
        updated = self._inventory_repository.update(book_id, fields)
        logger.info("Book updated", extra={"book_id": book_id, "seller_id": seller_id})
        return self._to_book_response(updated)

    def remove_book(self, seller_id: str, book_id: str) -> None:
        """Remove a book from a seller's inventory.

        Business rule: a book can only be removed if no copies have been sold
        (current_count == initial_count).

        Args:
            seller_id: UUID of the seller (for ownership verification).
            book_id: UUID of the book to remove.

        Raises:
            BookNotFoundError: If book does not exist or does not belong to seller.
            BookPartiallySoldError: If current_count < initial_count.
        """
        existing = self._inventory_repository.get_by_id(book_id)
        if existing is None or existing.get("seller_id") != seller_id:
            raise BookNotFoundError(book_id)

        current_count = int(existing["current_count"])
        initial_count = int(existing["initial_count"])
        if current_count < initial_count:
            raise BookPartiallySoldError(book_id)

        self._inventory_repository.delete(book_id)
        logger.info("Book removed from inventory", extra={"book_id": book_id, "seller_id": seller_id})

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_book_response(item: Dict) -> BookResponse:
        """Convert a raw DynamoDB item dict to a BookResponse with computed fields.

        DynamoDB returns numeric values as Decimal. This helper converts them to
        the correct Python types and computes the derived balance fields.

        Args:
            item: Raw Book dict from the DynamoDB repository.

        Returns:
            BookResponse with all fields populated including computed balances.
        """
        current_count = int(item["current_count"])
        initial_count = int(item["initial_count"])
        cost_per_book = float(item["cost_per_book"])
        selling_price = float(item["selling_price"])

        return BookResponse(
            book_id=item["book_id"],
            seller_id=item["seller_id"],
            bookstore_id=item["bookstore_id"],
            book_name=item["book_name"],
            language=item["language"],
            initial_count=initial_count,
            current_count=current_count,
            cost_per_book=cost_per_book,
            selling_price=selling_price,
            current_books_cost_balance=round(current_count * cost_per_book, 2),
            total_books_cost_balance=round(initial_count * cost_per_book, 2),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )
