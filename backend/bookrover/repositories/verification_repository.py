"""DynamoDB adapter for the email verification repository.

Stores one record per email address with a 6-digit code and an expiry
timestamp. Records are deleted by the router after successful consumption
to prevent code reuse.
"""

import logging
from typing import Optional

from bookrover.interfaces.abstract_verification_repository import (
    AbstractVerificationRepository,
)

logger = logging.getLogger(__name__)


class DynamoDBVerificationRepository(AbstractVerificationRepository):
    """Concrete DynamoDB implementation of AbstractVerificationRepository.

    The backing table uses ``email`` as the partition key (String).

    Args:
        table: A boto3 DynamoDB Table resource for the verifications table.
    """

    def __init__(self, table) -> None:
        self._table = table

    def save(self, email: str, code: str, expires_at: str) -> None:
        """Persist (or overwrite) a verification record.

        Args:
            email: Normalised email address — the partition key.
            code: 6-digit numeric string.
            expires_at: ISO 8601 UTC expiry timestamp.
        """
        self._table.put_item(
            Item={"email": email, "code": code, "expires_at": expires_at}
        )
        logger.info(
            "DynamoDB put_item",
            extra={"table": self._table.name, "operation": "save_verification"},
        )

    def get(self, email: str) -> Optional[dict]:
        """Fetch the verification record for the given email.

        Args:
            email: Normalised email address.

        Returns:
            Record dict or None if not found.
        """
        response = self._table.get_item(Key={"email": email})
        logger.info(
            "DynamoDB get_item",
            extra={"table": self._table.name, "operation": "get_verification"},
        )
        return response.get("Item")

    def delete(self, email: str) -> None:
        """Remove the verification record for the given email.

        Args:
            email: Normalised email address.
        """
        self._table.delete_item(Key={"email": email})
        logger.info(
            "DynamoDB delete_item",
            extra={"table": self._table.name, "operation": "delete_verification"},
        )
