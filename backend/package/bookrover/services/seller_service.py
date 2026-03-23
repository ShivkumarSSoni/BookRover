"""Business logic layer for the Seller Registration feature.

Owns all business rules for seller registration and profile retrieval.
Has zero knowledge of DynamoDB, HTTP, or Lambda — all external concerns
are injected through repository abstractions.
"""

import logging

from bookrover.exceptions.conflict import DuplicateEmailError
from bookrover.exceptions.not_found import (
    BookStoreNotFoundError,
    GroupLeaderNotFoundError,
    SellerNotFoundError,
)
from bookrover.interfaces.abstract_bookstore_repository import AbstractBookstoreRepository
from bookrover.interfaces.abstract_group_leader_repository import AbstractGroupLeaderRepository
from bookrover.interfaces.abstract_seller_repository import AbstractSellerRepository
from bookrover.interfaces.abstract_seller_service import AbstractSellerService
from bookrover.models.seller import SellerCreate, SellerResponse
from bookrover.utils.id_generator import generate_id
from bookrover.utils.timestamp import utc_now_iso

logger = logging.getLogger(__name__)

_SELLER_STATUS_ACTIVE = "active"


class SellerService(AbstractSellerService):
    """Concrete implementation of AbstractSellerService.

    Orchestrates seller registration by delegating all persistence calls
    to the injected repository abstractions.

    Args:
        seller_repository: Injected AbstractSellerRepository implementation.
        group_leader_repository: Injected AbstractGroupLeaderRepository implementation.
        bookstore_repository: Injected AbstractBookstoreRepository implementation.
    """

    def __init__(
        self,
        seller_repository: AbstractSellerRepository,
        group_leader_repository: AbstractGroupLeaderRepository,
        bookstore_repository: AbstractBookstoreRepository,
    ) -> None:
        self._seller_repository = seller_repository
        self._group_leader_repository = group_leader_repository
        self._bookstore_repository = bookstore_repository

    def register_seller(self, payload: SellerCreate) -> SellerResponse:
        """Validate and register a new seller.

        Business rules enforced:
        1. Email must not already be registered to another seller.
        2. group_leader_id must exist in the group leaders table.
        3. bookstore_id must exist in the bookstores table.

        Args:
            payload: Validated SellerCreate DTO from the HTTP layer.

        Returns:
            SellerResponse for the newly created seller.

        Raises:
            DuplicateEmailError: If the email is already registered.
            GroupLeaderNotFoundError: If group_leader_id does not exist.
            BookStoreNotFoundError: If bookstore_id does not exist.
        """
        normalised_email = payload.email.strip().lower()
        existing = self._seller_repository.get_by_email(normalised_email)
        if existing is not None:
            raise DuplicateEmailError(normalised_email)

        group_leader = self._group_leader_repository.get_by_id(payload.group_leader_id)
        if group_leader is None:
            raise GroupLeaderNotFoundError(payload.group_leader_id)

        bookstore = self._bookstore_repository.get_by_id(payload.bookstore_id)
        if bookstore is None:
            raise BookStoreNotFoundError(payload.bookstore_id)

        now = utc_now_iso()
        item = {
            "seller_id": generate_id(),
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "email": normalised_email,
            "group_leader_id": payload.group_leader_id,
            "bookstore_id": payload.bookstore_id,
            "status": _SELLER_STATUS_ACTIVE,
            "created_at": now,
            "updated_at": now,
        }
        persisted = self._seller_repository.create(item)
        logger.info("Seller registered", extra={"seller_id": persisted["seller_id"]})
        return SellerResponse(**persisted)

    def get_seller(self, seller_id: str) -> SellerResponse:
        """Fetch a seller profile by ID.

        Args:
            seller_id: UUID of the seller.

        Returns:
            SellerResponse for the seller.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
        """
        item = self._seller_repository.get_by_id(seller_id)
        if item is None:
            raise SellerNotFoundError(seller_id)
        return SellerResponse(**item)
