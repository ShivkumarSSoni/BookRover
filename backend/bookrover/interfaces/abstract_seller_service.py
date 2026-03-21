"""Abstract base class for the Seller service port.

Routers depend on this ABC — never on the concrete SellerService.
"""

from abc import ABC, abstractmethod

from bookrover.models.seller import SellerCreate, SellerResponse


class AbstractSellerService(ABC):
    """Port definition for all Seller business operations."""

    @abstractmethod
    def register_seller(self, payload: SellerCreate) -> SellerResponse:
        """Validate and register a new seller.

        Args:
            payload: Validated SellerCreate DTO.

        Returns:
            SellerResponse for the created seller.

        Raises:
            DuplicateEmailError: If email is already registered.
            GroupLeaderNotFoundError: If group_leader_id does not exist.
            BookStoreNotFoundError: If bookstore_id does not exist.
        """

    @abstractmethod
    def get_seller(self, seller_id: str) -> SellerResponse:
        """Fetch a seller by ID.

        Args:
            seller_id: UUID of the seller.

        Returns:
            SellerResponse for the seller.

        Raises:
            SellerNotFoundError: If seller does not exist.
        """
