"""Abstract base class for the email-verification repository port.

Services and routers depend on this ABC — never on the concrete DynamoDB
implementation. Each verification record holds a single 6-digit code for one
email address and expires after 10 minutes.
"""

from abc import ABC, abstractmethod
from typing import Optional


class AbstractVerificationRepository(ABC):
    """Port definition for email verification code persistence."""

    @abstractmethod
    def save(self, email: str, code: str, expires_at: str) -> None:
        """Persist (or overwrite) a verification record for the given email.

        Args:
            email: Normalised (lowercase) email address — the partition key.
            code: 6-digit numeric string.
            expires_at: ISO 8601 UTC timestamp when this code expires.
        """

    @abstractmethod
    def get(self, email: str) -> Optional[dict]:
        """Fetch the verification record for the given email.

        Args:
            email: Normalised email address.

        Returns:
            Dict with keys ``email``, ``code``, ``expires_at``, or None if
            no record exists for this email.
        """

    @abstractmethod
    def delete(self, email: str) -> None:
        """Remove the verification record for the given email.

        Called after the code is successfully consumed during seller registration
        to prevent code reuse.

        Args:
            email: Normalised email address.
        """
