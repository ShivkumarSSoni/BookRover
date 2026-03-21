"""FastAPI application factory for BookRover.

Creates and configures the FastAPI instance, registers all routers,
and applies middleware. The Mangum handler wraps the app for AWS Lambda.
"""

from contextlib import asynccontextmanager

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from bookrover.config import Settings


def _create_local_tables(settings: Settings) -> None:
    """Create DynamoDB tables in moto server for local development.

    Only runs when DYNAMODB_ENDPOINT_URL is set (i.e. local dev with moto server).
    In production Lambda, tables are pre-created via AWS Console / Terraform.

    Args:
        settings: Application settings containing table names and endpoint URL.
    """
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=settings.dynamodb_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )
    existing = {t.name for t in dynamodb.tables.all()}

    table_definitions = [
        {
            "TableName": settings.get_table_name("bookstores"),
            "KeySchema": [{"AttributeName": "bookstore_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "bookstore_id", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": settings.get_table_name("group-leaders"),
            "KeySchema": [{"AttributeName": "group_leader_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "group_leader_id", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": settings.get_table_name("sellers"),
            "KeySchema": [{"AttributeName": "seller_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "seller_id", "AttributeType": "S"},
                {"AttributeName": "group_leader_id", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "group-leader-id-index",
                    "KeySchema": [{"AttributeName": "group_leader_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        },
        {
            "TableName": settings.get_table_name("inventory"),
            "KeySchema": [{"AttributeName": "book_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "book_id", "AttributeType": "S"},
                {"AttributeName": "seller_id", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "seller-id-index",
                    "KeySchema": [{"AttributeName": "seller_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        },
        {
            "TableName": settings.get_table_name("sales"),
            "KeySchema": [{"AttributeName": "sale_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "sale_id", "AttributeType": "S"},
                {"AttributeName": "seller_id", "AttributeType": "S"},
                {"AttributeName": "bookstore_id", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "seller-id-index",
                    "KeySchema": [{"AttributeName": "seller_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "bookstore-id-index",
                    "KeySchema": [{"AttributeName": "bookstore_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
        },        {
            "TableName": settings.get_table_name("returns"),
            "KeySchema": [{"AttributeName": "return_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "return_id", "AttributeType": "S"},
                {"AttributeName": "seller_id", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "seller-id-index",
                    "KeySchema": [{"AttributeName": "seller_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
        },    ]

    for definition in table_definitions:
        if definition["TableName"] not in existing:
            dynamodb.create_table(**definition)


def create_app() -> FastAPI:
    """Create and configure the BookRover FastAPI application.

    Returns:
        Configured FastAPI instance with middleware and routers applied.
    """
    settings = Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.dynamodb_endpoint_url:
            _create_local_tables(settings)
        yield

    app = FastAPI(
        title="BookRover API",
        version="0.1.0",
        description="Backend API for the BookRover door-to-door book selling management app.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers are registered here as features are built:
    from bookrover.routers import admin, dashboard, inventory, lookup, returns, sales, sellers
    app.include_router(admin.router)
    app.include_router(sellers.router)
    app.include_router(lookup.router)
    app.include_router(inventory.router)
    app.include_router(sales.router)
    app.include_router(returns.router)
    app.include_router(returns.router)
    app.include_router(dashboard.router)

    return app


app = create_app()

# AWS Lambda entry point — Mangum translates API Gateway proxy events to ASGI.
handler = Mangum(app)
