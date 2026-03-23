"""Business logic layer for the Auth feature.

Resolves a BookRover identity (roles + IDs) from a verified email address.
Has zero knowledge of DynamoDB, HTTP, tokens, or Lambda — all external
concerns are injected through repository abstractions.
"""

import logging
from typing import List

from bookrover.interfaces.abstract_auth_service import AbstractAuthService
from bookrover.interfaces.abstract_group_leader_repository import AbstractGroupLeaderRepository
from bookrover.interfaces.abstract_seller_repository import AbstractSellerRepository
from bookrover.models.auth import MeResponse

logger = logging.getLogger(__name__)

_ROLE_ADMIN = "admin"
_ROLE_GROUP_LEADER = "group_leader"
_ROLE_SELLER = "seller"


class AuthService(AbstractAuthService):
    """Concrete implementation of AbstractAuthService.

    Performs role resolution by checking (in order):
    1. admin_emails config list → admin role
    2. group_leaders DynamoDB table → group_leader role
    3. sellers DynamoDB table → seller role

    Args:
        seller_repository: Injected AbstractSellerRepository.
        group_leader_repository: Injected AbstractGroupLeaderRepository.
        admin_emails: List of email addresses granted admin access via config.
    """

    def __init__(
        self,
        seller_repository: AbstractSellerRepository,
        group_leader_repository: AbstractGroupLeaderRepository,
        admin_emails: List[str],
    ) -> None:
        self._seller_repository = seller_repository
        self._group_leader_repository = group_leader_repository
        self._admin_emails = [e.strip().lower() for e in admin_emails]

    def get_me(self, email: str) -> MeResponse:
        """Resolve the BookRover identity for a given authenticated email.

        Checks admin_emails first (no DynamoDB call needed for admin detection).
        Admin users are returned immediately without further table lookups.
        Non-admin users may hold both group_leader and seller roles simultaneously.

        Args:
            email: Verified email address of the authenticated caller.

        Returns:
            MeResponse carrying roles, seller_id, and group_leader_id.
        """
        normalised_email = email.strip().lower()

        if normalised_email in self._admin_emails:
            logger.info("auth.get_me: admin role resolved", extra={"email": normalised_email})
            return MeResponse(email=email, roles=[_ROLE_ADMIN])

        roles: List[str] = []
        seller_id: str | None = None
        group_leader_id: str | None = None

        group_leader = self._group_leader_repository.get_by_email(normalised_email)
        if group_leader is not None:
            roles.append(_ROLE_GROUP_LEADER)
            group_leader_id = group_leader["group_leader_id"]
            logger.info(
                "auth.get_me: group_leader role resolved",
                extra={"email": normalised_email, "group_leader_id": group_leader_id},
            )

        seller = self._seller_repository.get_by_email(normalised_email)
        if seller is not None:
            roles.append(_ROLE_SELLER)
            seller_id = seller["seller_id"]
            logger.info(
                "auth.get_me: seller role resolved",
                extra={"email": normalised_email, "seller_id": seller_id},
            )

        return MeResponse(
            email=email,
            roles=roles,
            seller_id=seller_id,
            group_leader_id=group_leader_id,
        )
