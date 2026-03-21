"""Abstract base class for the Sale repository port.

Services depend on this ABC — never on the concrete DynamoDB implementation.
This enables unit testing with a mock repository (no AWS calls).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AbstractSaleRepository(ABC):
    """Port definition for all Sale data access operations."""

    @abstractmethod
    def create(self, item: Dict) -> Dict:
        """Persist a new Sale record.

        Args:
            item: Complete Sale dict including sale_id, seller_id, bookstore_id,
                  buyer details, sale_items, totals, and timestamps.

        Returns:
            The persisted item dict, identical to what was stored.
        """

    @abstractmethod
    def get_by_id(self, sale_id: str) -> Optional[Dict]:
        """Fetch a single Sale by its primary key.

        Args:
            sale_id: UUID string of the sale.

        Returns:
            The Sale dict, or None if not found.
        """

    @abstractmethod
    def list_by_seller(self, seller_id: str) -> List[Dict]:
        """List all Sales for a seller using the seller-id GSI.

        Args:
            seller_id: UUID of the seller.

        Returns:
            List of Sale dicts (may be empty).
        """
