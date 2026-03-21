"""DynamoDB adapter for the Inventory repository.

This is the only file in the `bookrover` package that calls DynamoDB
for Inventory (Book) operations. All access patterns are implemented here.
"""

import logging
from typing import Dict, List, Optional

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from bookrover.exceptions.not_found import BookNotFoundError
from bookrover.interfaces.abstract_inventory_repository import AbstractInventoryRepository

logger = logging.getLogger(__name__)

_SELLER_ID_GSI = "seller-id-index"


class DynamoDBInventoryRepository(AbstractInventoryRepository):
    """Concrete DynamoDB implementation of AbstractInventoryRepository.

    The DynamoDB table resource is injected via the constructor — never
    fetched internally — enabling easy test isolation using moto.

    Args:
        table: A boto3 DynamoDB Table resource for the inventory table.
    """

    def __init__(self, table) -> None:
        self._table = table

    def create(self, item: Dict) -> Dict:
        """Persist a new Book using a conditional put to prevent overwrites.

        Args:
            item: Complete Book dict including book_id, seller_id, bookstore_id, timestamps.

        Returns:
            The persisted item dict, identical to what was stored.
        """
        self._table.put_item(
            Item=item,
            ConditionExpression=Attr("book_id").not_exists(),
        )
        logger.info(
            "DynamoDB put_item",
            extra={"table": self._table.name, "operation": "create", "key": item["book_id"]},
        )
        return item

    def get_by_id(self, book_id: str) -> Optional[Dict]:
        """Fetch a Book by primary key.

        Args:
            book_id: UUID string of the book.

        Returns:
            The Book dict, or None if not found.
        """
        response = self._table.get_item(Key={"book_id": book_id})
        logger.debug(
            "DynamoDB get_item",
            extra={"table": self._table.name, "operation": "get_by_id", "key": book_id},
        )
        return response.get("Item")

    def list_by_seller(self, seller_id: str) -> List[Dict]:
        """List all Books for a seller by querying the seller-id GSI.

        Args:
            seller_id: UUID of the owning seller.

        Returns:
            List of Book dicts (may be empty).
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

    def update(self, book_id: str, fields: Dict) -> Dict:
        """Apply a partial update to an existing Book.

        Args:
            book_id: UUID of the book to update.
            fields: Dict of field names → new values (always includes updated_at).

        Returns:
            The full updated Book dict.

        Raises:
            BookNotFoundError: If no book exists with the given ID.
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
                Key={"book_id": book_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression=Attr("book_id").exists(),
                ReturnValues="ALL_NEW",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise BookNotFoundError(book_id) from exc
            raise

        logger.info(
            "DynamoDB update_item",
            extra={"table": self._table.name, "operation": "update", "key": book_id},
        )
        return response["Attributes"]

    def delete(self, book_id: str) -> None:
        """Delete a Book by primary key.

        Args:
            book_id: UUID of the book to delete.

        Raises:
            BookNotFoundError: If no book exists with the given ID.
        """
        try:
            self._table.delete_item(
                Key={"book_id": book_id},
                ConditionExpression=Attr("book_id").exists(),
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise BookNotFoundError(book_id) from exc
            raise

        logger.info(
            "DynamoDB delete_item",
            extra={"table": self._table.name, "operation": "delete", "key": book_id},
        )
