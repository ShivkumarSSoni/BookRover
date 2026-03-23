"""Abstract Base Class for the BookStore repository.

Defines the contract that any DynamoDB (or test-mock) implementation
must satisfy. The service layer depends only on this abstraction —
never on any concrete DynamoDB class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AbstractBookstoreRepository(ABC):
    """Port definition for BookStore data access.

    All implementations must store and retrieve BookStore records as
    typed dicts with the keys defined in the DynamoDB table schema.
    """

    @abstractmethod
    def create(self, item: Dict) -> Dict:
        """Persist a new BookStore record.

        Args:
            item: A complete BookStore dict (incl. bookstore_id, created_at, updated_at).

        Returns:
            The persisted item dict, identical to what was stored.
        """

    @abstractmethod
    def get_by_id(self, bookstore_id: str) -> Optional[Dict]:
        """Fetch a single BookStore by its primary key.

        Args:
            bookstore_id: UUID string of the bookstore.

        Returns:
            The BookStore dict, or None if not found.
        """

    @abstractmethod
    def list_all(self) -> List[Dict]:
        """Return all BookStore records.

        Returns:
            A list of BookStore dicts (may be empty).
        """

    @abstractmethod
    def update(self, bookstore_id: str, fields: Dict) -> Dict:
        """Apply a partial update to an existing BookStore.

        Args:
            bookstore_id: UUID string of the bookstore to update.
            fields: Dict of field names → new values to apply.

        Returns:
            The full updated BookStore dict.

        Raises:
            BookStoreNotFoundError: If no bookstore exists with the given ID.
        """

    @abstractmethod
    def delete(self, bookstore_id: str) -> None:
        """Delete a BookStore by its primary key.

        Args:
            bookstore_id: UUID string of the bookstore to delete.

        Raises:
            BookStoreNotFoundError: If no bookstore exists with the given ID.
        """
