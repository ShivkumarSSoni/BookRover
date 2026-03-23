"""Abstract base class for the Inventory repository port.

Services depend on this ABC — never on the concrete DynamoDB implementation.
This enables unit testing with a mock repository (no AWS calls).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AbstractInventoryRepository(ABC):
    """Port definition for all Inventory (Book) data access operations."""

    @abstractmethod
    def create(self, item: Dict) -> Dict:
        """Persist a new Book record.

        Args:
            item: Complete Book dict including book_id, seller_id, bookstore_id,
                  initial_count, current_count, cost_per_book, selling_price, timestamps.

        Returns:
            The persisted item dict, identical to what was stored.
        """

    @abstractmethod
    def get_by_id(self, book_id: str) -> Optional[Dict]:
        """Fetch a single Book by its primary key.

        Args:
            book_id: UUID string of the book.

        Returns:
            The Book dict, or None if not found.
        """

    @abstractmethod
    def list_by_seller(self, seller_id: str) -> List[Dict]:
        """List all Books for a seller using the seller-id GSI.

        Args:
            seller_id: UUID of the seller.

        Returns:
            List of Book dicts (may be empty).
        """

    @abstractmethod
    def update(self, book_id: str, fields: Dict) -> Dict:
        """Apply a partial update to an existing Book.

        Args:
            book_id: UUID of the book to update.
            fields: Dict of field names → new values (always includes updated_at).

        Returns:
            The full updated Book dict.

        Raises:
            BookNotFoundError: If no book exists with the given ID.
        """

    @abstractmethod
    def delete(self, book_id: str) -> None:
        """Delete a Book by primary key.

        Args:
            book_id: UUID of the book to delete.

        Raises:
            BookNotFoundError: If no book exists with the given ID.
        """

    @abstractmethod
    def decrement_count(self, book_id: str, quantity: int, updated_at: str) -> None:
        """Atomically decrement a Book's current_count by quantity.

        Args:
            book_id: UUID of the book.
            quantity: Number of copies to subtract from current_count.
            updated_at: ISO timestamp to write into the updated_at field.

        Raises:
            InsufficientInventoryError: If current_count < quantity at write time
                (guards against concurrent oversell).
            BookNotFoundError: If no book exists with the given ID.
        """
