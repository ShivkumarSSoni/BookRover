"""Abstract base class for the Return repository port.

Services depend on this ABC — never on the concrete DynamoDB implementation.
This enables unit testing with a mock repository (no AWS calls).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AbstractReturnRepository(ABC):
    """Port definition for all Return data access operations."""

    @abstractmethod
    def create(self, item: Dict) -> Dict:
        """Persist a new Return record.

        Args:
            item: Complete Return dict including return_id, seller_id, bookstore_id,
                  return_items, totals, status, and timestamps.

        Returns:
            The persisted item dict, identical to what was stored.
        """

    @abstractmethod
    def get_by_id(self, return_id: str) -> Optional[Dict]:
        """Fetch a single Return by its primary key.

        Args:
            return_id: UUID string of the return.

        Returns:
            The Return dict, or None if not found.
        """

    @abstractmethod
    def list_by_seller(self, seller_id: str) -> List[Dict]:
        """List all Returns for a seller using the seller-id GSI.

        Args:
            seller_id: UUID of the seller.

        Returns:
            List of Return dicts (may be empty).
        """
