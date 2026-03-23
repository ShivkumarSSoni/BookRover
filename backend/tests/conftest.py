"""Shared pytest fixtures for BookRover backend tests.

This is the single source of truth for test infrastructure. It provides:
  - A moto mock_aws fixture that creates all 7 BookRover DynamoDB tables.
  - Function scope (default): each test gets clean, empty tables.
  - No real AWS calls are ever made — moto intercepts all boto3 operations.

Environment variables are set before any bookrover imports to ensure
Settings resolves to 'test' environment and tables are named bookrover-*-test.
"""

import os

import boto3
import pytest
from moto import mock_aws

# Force test environment BEFORE any bookrover imports.
# This ensures Settings.app_env == "test" and table names resolve to
# bookrover-*-test, never touching dev or prod tables.
os.environ["APP_ENV"] = "test"
os.environ["DYNAMODB_REGION"] = "us-east-1"  # moto requires us-east-1
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# ── DynamoDB table definitions ────────────────────────────────────────────────
# Mirrors the data-models spec exactly: table names, PKs, and GSIs.
# GSI names follow kebab-case convention: e.g. 'seller-id-index'.
# ─────────────────────────────────────────────────────────────────────────────
_TABLE_DEFINITIONS: list[dict] = [
    {
        "TableName": "bookrover-admins-test",
        "KeySchema": [{"AttributeName": "admin_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "admin_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "bookrover-bookstores-test",
        "KeySchema": [{"AttributeName": "bookstore_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "bookstore_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "bookrover-group-leaders-test",
        "KeySchema": [{"AttributeName": "group_leader_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "group_leader_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "bookrover-sellers-test",
        "KeySchema": [{"AttributeName": "seller_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "seller_id", "AttributeType": "S"},
            {"AttributeName": "group_leader_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "group-leader-id-index",
                "KeySchema": [
                    {"AttributeName": "group_leader_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "bookrover-inventory-test",
        "KeySchema": [{"AttributeName": "book_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "book_id", "AttributeType": "S"},
            {"AttributeName": "seller_id", "AttributeType": "S"},
            {"AttributeName": "bookstore_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "seller-id-index",
                "KeySchema": [{"AttributeName": "seller_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "bookstore-id-index",
                "KeySchema": [
                    {"AttributeName": "bookstore_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "bookrover-sales-test",
        "KeySchema": [{"AttributeName": "sale_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "sale_id", "AttributeType": "S"},
            {"AttributeName": "seller_id", "AttributeType": "S"},
            {"AttributeName": "bookstore_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "seller-id-index",
                "KeySchema": [{"AttributeName": "seller_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "bookstore-id-index",
                "KeySchema": [
                    {"AttributeName": "bookstore_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "bookrover-returns-test",
        "KeySchema": [{"AttributeName": "return_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "return_id", "AttributeType": "S"},
            {"AttributeName": "seller_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "seller-id-index",
                "KeySchema": [{"AttributeName": "seller_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "bookrover-email-verifications-test",
        "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
]


@pytest.fixture
def dynamodb_tables():
    """Spin up all 7 BookRover DynamoDB tables in moto and yield the resource.

    Function-scoped (default): each test receives a completely fresh, empty
    set of tables. The mock_aws context is torn down after each test, so no
    state leaks between tests.

    Yields:
        boto3 DynamoDB ServiceResource connected to the moto mock backend.

    Usage in a test:
        def test_something(dynamodb_tables):
            table = dynamodb_tables.Table("bookrover-bookstores-test")
            table.put_item(Item={...})
    """
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        for table_def in _TABLE_DEFINITIONS:
            resource.create_table(**table_def)
        yield resource
