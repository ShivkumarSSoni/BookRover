"""DynamoDB adapter for the BookStore repository.

This is the only file in the `bookrover` package that calls DynamoDB
for BookStore operations. All access patterns are implemented here.
"""

import logging
from typing import Dict, List, Optional

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from bookrover.exceptions.not_found import BookStoreNotFoundError
from bookrover.interfaces.abstract_bookstore_repository import (
    AbstractBookstoreRepository,
)

logger = logging.getLogger(__name__)


class DynamoDBBookstoreRepository(AbstractBookstoreRepository):
    """Concrete DynamoDB implementation of AbstractBookstoreRepository.

    The DynamoDB table resource is injected via the constructor — never
    fetched internally — enabling easy test isolation using moto.

    Args:
        table: A boto3 DynamoDB Table resource for the bookstores table.
    """

    def __init__(self, table) -> None:
        self._table = table

    def create(self, item: Dict) -> Dict:
        """Persist a new BookStore using a conditional put to prevent overwrites.

        Args:
            item: Complete BookStore dict including bookstore_id, created_at, updated_at.

        Returns:
            The persisted item dict, identical to what was stored.
        """
        self._table.put_item(
            Item=item,
            ConditionExpression=Attr("bookstore_id").not_exists(),
        )
        logger.info(
            "DynamoDB put_item",
            extra={"table": self._table.name, "operation": "create", "key": item["bookstore_id"]},
        )
        return item

    def get_by_id(self, bookstore_id: str) -> Optional[Dict]:
        """Fetch a BookStore by primary key.

        Args:
            bookstore_id: UUID string of the bookstore.

        Returns:
            The BookStore dict, or None if not found.
        """
        response = self._table.get_item(Key={"bookstore_id": bookstore_id})
        logger.debug(
            "DynamoDB get_item",
            extra={"table": self._table.name, "operation": "get_by_id", "key": bookstore_id},
        )
        return response.get("Item")

    def list_all(self) -> List[Dict]:
        """Scan the table and return all BookStore records.

        Returns:
            List of BookStore dicts (may be empty).
        """
        items: List[Dict] = []
        kwargs: Dict = {}
        while True:
            response = self._table.scan(**kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key
        logger.debug("DynamoDB scan", extra={"table": self._table.name, "operation": "list_all"})
        return items

    def update(self, bookstore_id: str, fields: Dict) -> Dict:
        """Apply a partial update to an existing BookStore.

        Args:
            bookstore_id: UUID of the bookstore to update.
            fields: Dict of field names → new values to apply (always includes updated_at).

        Returns:
            The full updated BookStore dict.

        Raises:
            BookStoreNotFoundError: If no bookstore exists with the given ID.
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
                Key={"bookstore_id": bookstore_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression=Attr("bookstore_id").exists(),
                ReturnValues="ALL_NEW",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise BookStoreNotFoundError(bookstore_id) from exc
            raise

        logger.info(
            "DynamoDB update_item",
            extra={"table": self._table.name, "operation": "update", "key": bookstore_id},
        )
        return response["Attributes"]

    def delete(self, bookstore_id: str) -> None:
        """Delete a BookStore by primary key.

        Args:
            bookstore_id: UUID of the bookstore to delete.

        Raises:
            BookStoreNotFoundError: If no bookstore exists with the given ID.
        """
        try:
            self._table.delete_item(
                Key={"bookstore_id": bookstore_id},
                ConditionExpression=Attr("bookstore_id").exists(),
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise BookStoreNotFoundError(bookstore_id) from exc
            raise

        logger.info(
            "DynamoDB delete_item",
            extra={"table": self._table.name, "operation": "delete", "key": bookstore_id},
        )
