"""Abstract Base Class for the GroupLeader repository.

Defines the contract that any DynamoDB (or test-mock) implementation
must satisfy. The service layer depends only on this abstraction —
never on any concrete DynamoDB class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class AbstractGroupLeaderRepository(ABC):
    """Port definition for GroupLeader data access.

    All implementations must store and retrieve GroupLeader records as
    typed dicts with the keys defined in the DynamoDB table schema.
    """

    @abstractmethod
    def create(self, item: Dict) -> Dict:
        """Persist a new GroupLeader record.

        Args:
            item: A complete GroupLeader dict (incl. group_leader_id, created_at, updated_at).

        Returns:
            The persisted item dict, identical to what was stored.
        """

    @abstractmethod
    def get_by_id(self, group_leader_id: str) -> Optional[Dict]:
        """Fetch a single GroupLeader by its primary key.

        Args:
            group_leader_id: UUID string of the group leader.

        Returns:
            The GroupLeader dict, or None if not found.
        """

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Dict]:
        """Fetch a GroupLeader by email for uniqueness validation.

        Args:
            email: The email address to look up.

        Returns:
            The GroupLeader dict, or None if no match found.
        """

    @abstractmethod
    def list_all(self) -> List[Dict]:
        """Return all GroupLeader records.

        Returns:
            A list of GroupLeader dicts (may be empty).
        """

    @abstractmethod
    def update(self, group_leader_id: str, fields: Dict) -> Dict:
        """Apply a partial update to an existing GroupLeader.

        Args:
            group_leader_id: UUID string of the group leader to update.
            fields: Dict of field names → new values to apply.

        Returns:
            The full updated GroupLeader dict.

        Raises:
            GroupLeaderNotFoundError: If no group leader exists with the given ID.
        """

    @abstractmethod
    def delete(self, group_leader_id: str) -> None:
        """Delete a GroupLeader by its primary key.

        Args:
            group_leader_id: UUID string of the group leader to delete.

        Raises:
            GroupLeaderNotFoundError: If no group leader exists with the given ID.
        """

    @abstractmethod
    def count_active_sellers(self, group_leader_id: str) -> int:
        """Count sellers currently assigned to this group leader.

        Used by the service before deletion to enforce the business rule
        that a group leader with active sellers cannot be deleted.

        Args:
            group_leader_id: UUID string of the group leader.

        Returns:
            Number of sellers (int) linked to this group leader.
        """
