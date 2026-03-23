"""Abstract base class for the Inventory service port.

Routers depend on this ABC — never on the concrete InventoryService.
"""

from abc import ABC, abstractmethod

from bookrover.models.inventory import BookCreate, BookResponse, BookUpdate, InventoryListResponse


class AbstractInventoryService(ABC):
    """Port definition for all Inventory business operations."""

    @abstractmethod
    def add_book(self, seller_id: str, payload: BookCreate) -> BookResponse:
        """Add a new book to a seller's inventory.

        Args:
            seller_id: UUID of the seller.
            payload: Validated BookCreate DTO.

        Returns:
            BookResponse for the created book.

        Raises:
            SellerNotFoundError: If seller does not exist.
        """

    @abstractmethod
    def get_inventory(self, seller_id: str) -> InventoryListResponse:
        """Return the full inventory for a seller with aggregate summary.

        Args:
            seller_id: UUID of the seller.

        Returns:
            InventoryListResponse with books list and summary.

        Raises:
            SellerNotFoundError: If seller does not exist.
        """

    @abstractmethod
    def update_book(self, seller_id: str, book_id: str, payload: BookUpdate) -> BookResponse:
        """Apply a partial update to a book in a seller's inventory.

        Args:
            seller_id: UUID of the seller (for ownership verification).
            book_id: UUID of the book to update.
            payload: Validated BookUpdate DTO.

        Returns:
            Updated BookResponse with recomputed balance fields.

        Raises:
            BookNotFoundError: If book does not exist or does not belong to seller.
        """

    @abstractmethod
    def remove_book(self, seller_id: str, book_id: str) -> None:
        """Remove a book from a seller's inventory.

        Args:
            seller_id: UUID of the seller (for ownership verification).
            book_id: UUID of the book to remove.

        Raises:
            BookNotFoundError: If book does not exist or does not belong to seller.
            BookPartiallySoldError: If the book has been partially sold
                (current_count < initial_count).
        """
