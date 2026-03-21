"""Abstract Base Class for the Admin service.

Defines the contract that AdminService must implement. Routers depend
on this abstraction — never on the concrete AdminService class directly.
"""

from abc import ABC, abstractmethod
from typing import List

from bookrover.models.bookstore import (
    BookStoreCreate,
    BookStoreResponse,
    BookStoreUpdate,
)
from bookrover.models.group_leader import (
    GroupLeaderCreate,
    GroupLeaderResponse,
    GroupLeaderUpdate,
)


class AbstractAdminService(ABC):
    """Port definition for Admin business operations.

    Covers BookStore and GroupLeader CRUD operations for the Admin feature.
    """

    # ------------------------------------------------------------------
    # BookStore operations
    # ------------------------------------------------------------------

    @abstractmethod
    def create_bookstore(self, payload: BookStoreCreate) -> BookStoreResponse:
        """Create a new BookStore.

        Args:
            payload: Validated BookStoreCreate DTO.

        Returns:
            BookStoreResponse with the persisted bookstore data.
        """

    @abstractmethod
    def list_bookstores(self) -> List[BookStoreResponse]:
        """Return all BookStores.

        Returns:
            List of BookStoreResponse DTOs (may be empty).
        """

    @abstractmethod
    def update_bookstore(self, bookstore_id: str, payload: BookStoreUpdate) -> BookStoreResponse:
        """Apply a partial update to a BookStore.

        Args:
            bookstore_id: UUID of the bookstore to update.
            payload: Validated BookStoreUpdate DTO (only non-None fields are applied).

        Returns:
            Updated BookStoreResponse.

        Raises:
            BookStoreNotFoundError: If bookstore_id does not exist.
        """

    @abstractmethod
    def delete_bookstore(self, bookstore_id: str) -> None:
        """Delete a BookStore.

        Args:
            bookstore_id: UUID of the bookstore to delete.

        Raises:
            BookStoreNotFoundError: If bookstore_id does not exist.
        """

    # ------------------------------------------------------------------
    # GroupLeader operations
    # ------------------------------------------------------------------

    @abstractmethod
    def create_group_leader(self, payload: GroupLeaderCreate) -> GroupLeaderResponse:
        """Create a new GroupLeader.

        Args:
            payload: Validated GroupLeaderCreate DTO.

        Returns:
            GroupLeaderResponse with the persisted group leader data.

        Raises:
            DuplicateEmailError: If email already exists.
        """

    @abstractmethod
    def list_group_leaders(self) -> List[GroupLeaderResponse]:
        """Return all GroupLeaders.

        Returns:
            List of GroupLeaderResponse DTOs (may be empty).
        """

    @abstractmethod
    def update_group_leader(self, group_leader_id: str, payload: GroupLeaderUpdate) -> GroupLeaderResponse:
        """Apply a partial update to a GroupLeader.

        Args:
            group_leader_id: UUID of the group leader to update.
            payload: Validated GroupLeaderUpdate DTO (only non-None fields are applied).

        Returns:
            Updated GroupLeaderResponse.

        Raises:
            GroupLeaderNotFoundError: If group_leader_id does not exist.
        """

    @abstractmethod
    def delete_group_leader(self, group_leader_id: str) -> None:
        """Delete a GroupLeader.

        Args:
            group_leader_id: UUID of the group leader to delete.

        Raises:
            GroupLeaderNotFoundError: If group_leader_id does not exist.
            ActiveSellersExistError: If the group leader has active sellers assigned.
        """
