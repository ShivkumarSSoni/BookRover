"""Abstract base class for the Auth service port.

Routers depend on this ABC — never on the concrete AuthService.
"""

from abc import ABC, abstractmethod

from bookrover.models.auth import MeResponse


class AbstractAuthService(ABC):
    """Port definition for all Auth business operations."""

    @abstractmethod
    def get_me(self, email: str) -> MeResponse:
        """Resolve the BookRover identity for a given authenticated email.

        Checks in priority order:
        1. ADMIN_EMAILS env var → role 'admin'
        2. group_leaders DynamoDB table → role 'group_leader'
        3. sellers DynamoDB table → role 'seller'
        A user may hold both 'group_leader' and 'seller' simultaneously.
        An empty roles list means the user is new and has not registered yet.

        Args:
            email: Verified email address of the authenticated caller.

        Returns:
            MeResponse carrying roles, seller_id, and group_leader_id.
        """
