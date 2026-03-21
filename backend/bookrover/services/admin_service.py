"""Business logic layer for the Admin feature.

Owns all business rules for BookStore and GroupLeader CRUD operations.
Has zero knowledge of DynamoDB, HTTP, or Lambda — all external concerns
are injected through repository abstractions.
"""

import logging
from typing import List

from bookrover.exceptions.conflict import ActiveSellersExistError, DuplicateEmailError
from bookrover.exceptions.not_found import (
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
)
from bookrover.interfaces.abstract_admin_service import AbstractAdminService
from bookrover.interfaces.abstract_bookstore_repository import (
    AbstractBookstoreRepository,
)
from bookrover.interfaces.abstract_group_leader_repository import (
    AbstractGroupLeaderRepository,
)
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
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso

logger = logging.getLogger(__name__)


class AdminService(AbstractAdminService):
    """Concrete implementation of AbstractAdminService.

    Orchestrates BookStore and GroupLeader operations by delegating all
    persistence calls to the injected repository abstractions.

    Args:
        bookstore_repository: Injected AbstractBookstoreRepository implementation.
        group_leader_repository: Injected AbstractGroupLeaderRepository implementation.
    """

    def __init__(
        self,
        bookstore_repository: AbstractBookstoreRepository,
        group_leader_repository: AbstractGroupLeaderRepository,
    ) -> None:
        self._bookstore_repository = bookstore_repository
        self._group_leader_repository = group_leader_repository

    # ------------------------------------------------------------------
    # BookStore operations
    # ------------------------------------------------------------------

    def create_bookstore(self, payload: BookStoreCreate) -> BookStoreResponse:
        """Create a new BookStore record.

        Args:
            payload: Validated BookStoreCreate DTO.

        Returns:
            BookStoreResponse with the persisted bookstore data.
        """
        now = utc_now_iso()
        item = {
            "bookstore_id": generate_id(),
            "store_name": payload.store_name,
            "owner_name": payload.owner_name,
            "address": payload.address,
            "phone_number": payload.phone_number,
            "created_at": now,
            "updated_at": now,
        }
        persisted = self._bookstore_repository.create(item)
        logger.info("BookStore created", extra={"bookstore_id": persisted["bookstore_id"]})
        return BookStoreResponse(**persisted)

    def list_bookstores(self) -> List[BookStoreResponse]:
        """Return all BookStores.

        Returns:
            List of BookStoreResponse DTOs (may be empty).
        """
        items = self._bookstore_repository.list_all()
        return [BookStoreResponse(**item) for item in items]

    def update_bookstore(self, bookstore_id: str, payload: BookStoreUpdate) -> BookStoreResponse:
        """Apply a partial update to a BookStore.

        Only fields explicitly set in the payload (non-None) are updated.
        updated_at is always refreshed.

        Args:
            bookstore_id: UUID of the bookstore to update.
            payload: Validated BookStoreUpdate DTO.

        Returns:
            Updated BookStoreResponse.

        Raises:
            BookStoreNotFoundError: If bookstore_id does not exist.
        """
        fields = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not fields:
            existing = self._bookstore_repository.get_by_id(bookstore_id)
            if existing is None:
                raise BookStoreNotFoundError(bookstore_id)
            return BookStoreResponse(**existing)

        fields["updated_at"] = utc_now_iso()
        updated = self._bookstore_repository.update(bookstore_id, fields)
        logger.info("BookStore updated", extra={"bookstore_id": bookstore_id})
        return BookStoreResponse(**updated)

    def delete_bookstore(self, bookstore_id: str) -> None:
        """Delete a BookStore.

        Args:
            bookstore_id: UUID of the bookstore to delete.

        Raises:
            BookStoreNotFoundError: If bookstore_id does not exist.
        """
        self._bookstore_repository.delete(bookstore_id)
        logger.info("BookStore deleted", extra={"bookstore_id": bookstore_id})

    # ------------------------------------------------------------------
    # GroupLeader operations
    # ------------------------------------------------------------------

    def create_group_leader(self, payload: GroupLeaderCreate) -> GroupLeaderResponse:
        """Create a new GroupLeader, enforcing email uniqueness.

        Args:
            payload: Validated GroupLeaderCreate DTO.

        Returns:
            GroupLeaderResponse with the persisted group leader data.

        Raises:
            DuplicateEmailError: If the email address is already registered.
        """
        existing = self._group_leader_repository.get_by_email(payload.email)
        if existing is not None:
            raise DuplicateEmailError(payload.email)

        now = utc_now_iso()
        item = {
            "group_leader_id": generate_id(),
            "name": payload.name,
            "email": payload.email,
            "bookstore_ids": payload.bookstore_ids,
            "created_at": now,
            "updated_at": now,
        }
        persisted = self._group_leader_repository.create(item)
        logger.info("GroupLeader created", extra={"group_leader_id": persisted["group_leader_id"]})
        return GroupLeaderResponse(**persisted)

    def list_group_leaders(self) -> List[GroupLeaderResponse]:
        """Return all GroupLeaders.

        Returns:
            List of GroupLeaderResponse DTOs (may be empty).
        """
        items = self._group_leader_repository.list_all()
        return [GroupLeaderResponse(**item) for item in items]

    def update_group_leader(self, group_leader_id: str, payload: GroupLeaderUpdate) -> GroupLeaderResponse:
        """Apply a partial update to a GroupLeader.

        Only fields explicitly set in the payload (non-None) are updated.
        updated_at is always refreshed.

        Args:
            group_leader_id: UUID of the group leader to update.
            payload: Validated GroupLeaderUpdate DTO.

        Returns:
            Updated GroupLeaderResponse.

        Raises:
            GroupLeaderNotFoundError: If group_leader_id does not exist.
        """
        fields = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not fields:
            existing = self._group_leader_repository.get_by_id(group_leader_id)
            if existing is None:
                raise GroupLeaderNotFoundError(group_leader_id)
            return GroupLeaderResponse(**existing)

        fields["updated_at"] = utc_now_iso()
        updated = self._group_leader_repository.update(group_leader_id, fields)
        logger.info("GroupLeader updated", extra={"group_leader_id": group_leader_id})
        return GroupLeaderResponse(**updated)

    def delete_group_leader(self, group_leader_id: str) -> None:
        """Delete a GroupLeader, enforcing no active sellers constraint.

        Args:
            group_leader_id: UUID of the group leader to delete.

        Raises:
            GroupLeaderNotFoundError: If group_leader_id does not exist.
            ActiveSellersExistError: If the group leader has sellers assigned.
        """
        seller_count = self._group_leader_repository.count_active_sellers(group_leader_id)
        if seller_count > 0:
            raise ActiveSellersExistError(group_leader_id, seller_count)

        self._group_leader_repository.delete(group_leader_id)
        logger.info("GroupLeader deleted", extra={"group_leader_id": group_leader_id})
