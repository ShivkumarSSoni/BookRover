"""Abstract base class for the Seller repository port.

Services depend on this ABC — never on the concrete DynamoDB implementation.
This enables unit testing with a mock repository (no AWS calls).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AbstractSellerRepository(ABC):
    """Port definition for all Seller data access operations."""

    @abstractmethod
    def create(self, item: Dict) -> Dict:
        """Persist a new Seller record.

        Args:
            item: Complete Seller dict including seller_id, timestamps, and status.

        Returns:
            The persisted item dict.
        """

    @abstractmethod
    def get_by_id(self, seller_id: str) -> Optional[Dict]:
        """Fetch a Seller by primary key.

        Args:
            seller_id: UUID of the seller.

        Returns:
            The Seller dict, or None if not found.
        """

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Dict]:
        """Fetch a Seller by email address (for duplicate-email check).

        Args:
            email: The email address to look up.

        Returns:
            The Seller dict, or None if not found.
        """

    @abstractmethod
    def list_by_group_leader(self, group_leader_id: str) -> List[Dict]:
        """List all sellers assigned to a specific group leader (via GSI).

        Args:
            group_leader_id: UUID of the group leader.

        Returns:
            List of Seller dicts.
        """

    @abstractmethod
    def update(self, seller_id: str, fields: Dict) -> Dict:
        """Apply a partial update to an existing Seller.

        Args:
            seller_id: UUID of the seller to update.
            fields: Dict of field names → new values (always includes updated_at).

        Returns:
            The full updated Seller dict.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
        """
