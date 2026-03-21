"""DynamoDB adapter for the Return repository.

This is the only file in the `bookrover` package that calls DynamoDB
for Return operations. All access patterns are implemented here.
"""

import logging
from typing import Dict, List, Optional

from boto3.dynamodb.conditions import Attr, Key

from bookrover.interfaces.abstract_return_repository import AbstractReturnRepository

logger = logging.getLogger(__name__)

_SELLER_ID_GSI = "seller-id-index"


class DynamoDBReturnRepository(AbstractReturnRepository):
    """Concrete DynamoDB implementation of AbstractReturnRepository.

    The DynamoDB table resource is injected via the constructor — never
    fetched internally — enabling easy test isolation using moto.

    Args:
        table: A boto3 DynamoDB Table resource for the returns table.
    """

    def __init__(self, table) -> None:
        self._table = table

    def create(self, item: Dict) -> Dict:
        """Persist a new Return record using a conditional put to prevent overwrites.

        Args:
            item: Complete Return dict including return_id, seller_id, bookstore_id,
                  return_items list, totals, status, and timestamps.

        Returns:
            The persisted item dict, identical to what was stored.
        """
        self._table.put_item(
            Item=item,
            ConditionExpression=Attr("return_id").not_exists(),
        )
        logger.info(
            "DynamoDB put_item",
            extra={"table": self._table.name, "operation": "create", "key": item["return_id"]},
        )
        return item

    def get_by_id(self, return_id: str) -> Optional[Dict]:
        """Fetch a Return by primary key.

        Args:
            return_id: UUID string of the return.

        Returns:
            The Return dict, or None if not found.
        """
        response = self._table.get_item(Key={"return_id": return_id})
        logger.debug(
            "DynamoDB get_item",
            extra={"table": self._table.name, "operation": "get_by_id", "key": return_id},
        )
        return response.get("Item")

    def list_by_seller(self, seller_id: str) -> List[Dict]:
        """List all Returns for a seller by querying the seller-id GSI.

        Args:
            seller_id: UUID of the owning seller.

        Returns:
            List of Return dicts (may be empty).
        """
        response = self._table.query(
            IndexName=_SELLER_ID_GSI,
            KeyConditionExpression=Key("seller_id").eq(seller_id),
        )
        logger.debug(
            "DynamoDB query",
            extra={"table": self._table.name, "operation": "list_by_seller", "key": seller_id},
        )
        return response.get("Items", [])
