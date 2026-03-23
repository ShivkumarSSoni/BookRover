"""Shared FastAPI dependency providers for BookRover.

This module is the dependency injection entry point. All Depends() used
across routers are defined here. FastAPI builds the full dependency graph
(Settings → DynamoDB resource → Repository → Service) at request time,
injecting the correct concrete implementation into each layer.
"""

from functools import lru_cache

import boto3
from fastapi import Depends

from bookrover.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Return the application Settings singleton.

    lru_cache ensures Settings is parsed from environment variables exactly
    once per process lifetime, not on every request.

    Returns:
        Cached Settings instance.
    """
    return Settings()


def get_dynamodb_resource(
    settings: Settings = Depends(get_settings),
):
    """Provide a boto3 DynamoDB resource for the current environment.

    Uses the endpoint URL from settings when set (moto_server for local dev).
    In Lambda, no endpoint URL is configured — the standard AWS endpoint is used.

    Args:
        settings: Injected Settings instance (via Depends).

    Returns:
        boto3 DynamoDB ServiceResource.
    """
    kwargs: dict = {"region_name": settings.dynamodb_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    return boto3.resource("dynamodb", **kwargs)
