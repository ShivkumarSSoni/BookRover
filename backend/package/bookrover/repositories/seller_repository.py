"""DynamoDB adapter for the Seller repository.

This is the only file in the `bookrover` package that calls DynamoDB
for Seller operations. All access patterns are implemented here.
"""

import logging
from typing import Dict, List, Optional

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from bookrover.exceptions.not_found import SellerNotFoundError
from bookrover.interfaces.abstract_seller_repository import AbstractSellerRepository

logger = logging.getLogger(__name__)

_GROUP_LEADER_ID_GSI = "group-leader-id-index"


class DynamoDBSellerRepository(AbstractSellerRepository):
    """Concrete DynamoDB implementation of AbstractSellerRepository.

    Args:
        table: A boto3 DynamoDB Table resource for the sellers table.
    """

    def __init__(self, table) -> None:
        self._table = table

    def create(self, item: Dict) -> Dict:
        """Persist a new Seller using a conditional put to prevent overwrites.

        Args:
            item: Complete Seller dict including seller_id, timestamps, and status.

        Returns:
            The persisted item dict.
        """
        self._table.put_item(
            Item=item,
            ConditionExpression=Attr("seller_id").not_exists(),
        )
        logger.info(
            "DynamoDB put_item",
            extra={"table": self._table.name, "operation": "create", "key": item["seller_id"]},
        )
        return item

    def get_by_id(self, seller_id: str) -> Optional[Dict]:
        """Fetch a Seller by primary key.

        Args:
            seller_id: UUID of the seller.

        Returns:
            The Seller dict, or None if not found.
        """
        response = self._table.get_item(Key={"seller_id": seller_id})
        logger.info(
            "DynamoDB get_item",
            extra={"table": self._table.name, "operation": "get_by_id", "key": seller_id},
        )
        return response.get("Item")

    def get_by_email(self, email: str) -> Optional[Dict]:
        """Scan for a Seller by email address.

        Uses a FilterExpression scan — acceptable since this is called only
        during registration (write path) and the sellers table is small.

        Args:
            email: The email address to look up.

        Returns:
            The Seller dict, or None if not found.
        """
        response = self._table.scan(FilterExpression=Attr("email").eq(email))
        logger.info(
            "DynamoDB scan",
            extra={"table": self._table.name, "operation": "get_by_email"},
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def list_by_group_leader(self, group_leader_id: str) -> List[Dict]:
        """List all sellers for a group leader using the GSI.

        Args:
            group_leader_id: UUID of the group leader.

        Returns:
            List of Seller dicts.
        """
        response = self._table.query(
            IndexName=_GROUP_LEADER_ID_GSI,
            KeyConditionExpression=Key("group_leader_id").eq(group_leader_id),
        )
        logger.info(
            "DynamoDB query",
            extra={
                "table": self._table.name,
                "operation": "list_by_group_leader",
                "key": group_leader_id,
            },
        )
        return response.get("Items", [])

    def update(self, seller_id: str, fields: Dict) -> Dict:
        """Apply a partial update to an existing Seller.

        Args:
            seller_id: UUID of the seller to update.
            fields: Dict of field names → new values (always includes updated_at).

        Returns:
            The full updated Seller dict.

        Raises:
            SellerNotFoundError: If no seller exists with the given ID.
        """
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        for key, value in fields.items():
            name_placeholder = f"#n_{key}"
            value_placeholder = f":v_{key}"
            update_expression_parts.append(f"{name_placeholder} = {value_placeholder}")
            expression_attribute_names[name_placeholder] = key
            expression_attribute_values[value_placeholder] = value

        update_expression = "SET " + ", ".join(update_expression_parts)

        try:
            response = self._table.update_item(
                Key={"seller_id": seller_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression=Attr("seller_id").exists(),
                ReturnValues="ALL_NEW",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise SellerNotFoundError(seller_id) from exc
            raise

        logger.info(
            "DynamoDB update_item",
            extra={"table": self._table.name, "operation": "update", "key": seller_id},
        )
        return response["Attributes"]
