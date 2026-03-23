"""DynamoDB adapter for the Sale repository.

This is the only file in the `bookrover` package that calls DynamoDB
for Sale operations. All access patterns are implemented here.
"""

import logging
from typing import Dict, List, Optional

from boto3.dynamodb.conditions import Key

from bookrover.interfaces.abstract_sale_repository import AbstractSaleRepository

logger = logging.getLogger(__name__)

_SELLER_ID_GSI = "seller-id-index"


class DynamoDBSaleRepository(AbstractSaleRepository):
    """Concrete DynamoDB implementation of AbstractSaleRepository.

    The DynamoDB table resource is injected via the constructor — never
    fetched internally — enabling easy test isolation using moto.

    Args:
        table: A boto3 DynamoDB Table resource for the sales table.
    """

    def __init__(self, table) -> None:
        self._table = table

    def create(self, item: Dict) -> Dict:
        """Persist a new Sale record.

        Args:
            item: Complete Sale dict including sale_id, buyer details, sale_items.

        Returns:
            The persisted item dict, identical to what was stored.
        """
        self._table.put_item(Item=item)
        logger.info(
            "DynamoDB put_item",
            extra={"table": self._table.name, "operation": "create", "key": item["sale_id"]},
        )
        return item

    def get_by_id(self, sale_id: str) -> Optional[Dict]:
        """Fetch a Sale by primary key.

        Args:
            sale_id: UUID string of the sale.

        Returns:
            The Sale dict, or None if not found.
        """
        response = self._table.get_item(Key={"sale_id": sale_id})
        logger.debug(
            "DynamoDB get_item",
            extra={"table": self._table.name, "operation": "get_by_id", "key": sale_id},
        )
        return response.get("Item")

    def list_by_seller(self, seller_id: str) -> List[Dict]:
        """List all Sales for a seller by querying the seller-id GSI.

        Args:
            seller_id: UUID of the owning seller.

        Returns:
            List of Sale dicts (may be empty).
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
