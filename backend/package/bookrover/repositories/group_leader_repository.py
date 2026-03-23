"""DynamoDB adapter for the GroupLeader repository.

This is the only file in the `bookrover` package that calls DynamoDB
for GroupLeader operations. All access patterns are implemented here.
"""

import logging
from typing import Dict, List, Optional

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from bookrover.exceptions.not_found import GroupLeaderNotFoundError
from bookrover.interfaces.abstract_group_leader_repository import (
    AbstractGroupLeaderRepository,
)

logger = logging.getLogger(__name__)

# GSI used for fetching sellers by group_leader_id (in the sellers table).
# count_active_sellers queries the sellers table, not the group leaders table.
_GROUP_LEADER_ID_GSI = "group-leader-id-index"


class DynamoDBGroupLeaderRepository(AbstractGroupLeaderRepository):
    """Concrete DynamoDB implementation of AbstractGroupLeaderRepository.

    The DynamoDB table resources are injected via the constructor — never
    fetched internally — enabling easy test isolation using moto.

    Args:
        table: A boto3 DynamoDB Table resource for the group leaders table.
        sellers_table: A boto3 DynamoDB Table resource for the sellers table,
            used only to count active sellers before deletion.
    """

    def __init__(self, table, sellers_table) -> None:
        self._table = table
        self._sellers_table = sellers_table

    def create(self, item: Dict) -> Dict:
        """Persist a new GroupLeader.

        Args:
            item: Complete GroupLeader dict including group_leader_id, created_at, updated_at.

        Returns:
            The persisted item dict, identical to what was stored.
        """
        self._table.put_item(
            Item=item,
            ConditionExpression=Attr("group_leader_id").not_exists(),
        )
        logger.info(
            "DynamoDB put_item",
            extra={"table": self._table.name, "operation": "create", "key": item["group_leader_id"]},
        )
        return item

    def get_by_id(self, group_leader_id: str) -> Optional[Dict]:
        """Fetch a GroupLeader by primary key.

        Args:
            group_leader_id: UUID string of the group leader.

        Returns:
            The GroupLeader dict, or None if not found.
        """
        response = self._table.get_item(Key={"group_leader_id": group_leader_id})
        logger.debug(
            "DynamoDB get_item",
            extra={"table": self._table.name, "operation": "get_by_id", "key": group_leader_id},
        )
        return response.get("Item")

    def get_by_email(self, email: str) -> Optional[Dict]:
        """Fetch a GroupLeader by email using a table scan with FilterExpression.

        GroupLeader emails must be unique. A scan is acceptable here because
        the Admin feature is low-frequency and the group leaders table is small.

        Args:
            email: Email address to look up.

        Returns:
            The GroupLeader dict, or None if not found.
        """
        response = self._table.scan(
            FilterExpression=Attr("email").eq(email),
        )
        items = response.get("Items", [])
        logger.debug(
            "DynamoDB scan (by email)",
            extra={"table": self._table.name, "operation": "get_by_email"},
        )
        return items[0] if items else None

    def list_all(self) -> List[Dict]:
        """Scan the table and return all GroupLeader records.

        Returns:
            List of GroupLeader dicts (may be empty).
        """
        response = self._table.scan()
        logger.debug(
            "DynamoDB scan",
            extra={"table": self._table.name, "operation": "list_all"},
        )
        return response.get("Items", [])

    def update(self, group_leader_id: str, fields: Dict) -> Dict:
        """Apply a partial update to an existing GroupLeader.

        Args:
            group_leader_id: UUID of the group leader to update.
            fields: Dict of field names → new values (always includes updated_at).

        Returns:
            The full updated GroupLeader dict.

        Raises:
            GroupLeaderNotFoundError: If no group leader exists with the given ID.
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
                Key={"group_leader_id": group_leader_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ConditionExpression=Attr("group_leader_id").exists(),
                ReturnValues="ALL_NEW",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise GroupLeaderNotFoundError(group_leader_id) from exc
            raise

        logger.info(
            "DynamoDB update_item",
            extra={"table": self._table.name, "operation": "update", "key": group_leader_id},
        )
        return response["Attributes"]

    def delete(self, group_leader_id: str) -> None:
        """Delete a GroupLeader by primary key.

        Args:
            group_leader_id: UUID of the group leader to delete.

        Raises:
            GroupLeaderNotFoundError: If no group leader exists with the given ID.
        """
        try:
            self._table.delete_item(
                Key={"group_leader_id": group_leader_id},
                ConditionExpression=Attr("group_leader_id").exists(),
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise GroupLeaderNotFoundError(group_leader_id) from exc
            raise

        logger.info(
            "DynamoDB delete_item",
            extra={"table": self._table.name, "operation": "delete", "key": group_leader_id},
        )

    def count_active_sellers(self, group_leader_id: str) -> int:
        """Count sellers assigned to this group leader via the sellers GSI.

        Queries `group-leader-id-index` on the sellers table to count
        how many sellers are currently linked to this group leader.

        Args:
            group_leader_id: UUID of the group leader.

        Returns:
            Number of sellers (int) linked to this group leader.
        """
        from boto3.dynamodb.conditions import Key

        response = self._sellers_table.query(
            IndexName=_GROUP_LEADER_ID_GSI,
            KeyConditionExpression=Key("group_leader_id").eq(group_leader_id),
            Select="COUNT",
        )
        logger.debug(
            "DynamoDB query (count sellers)",
            extra={"table": self._sellers_table.name, "operation": "count_active_sellers", "key": group_leader_id},
        )
        return response.get("Count", 0)
