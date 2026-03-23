"""Lookup router — public endpoints for Seller registration dropdowns.

Provides read-only endpoints used by the frontend to populate the
registration form without authentication.

Dependency graph (built at request time by FastAPI):
  DynamoDB resource → repositories → this router (no service layer needed
  for simple read-only data assembly)
"""

import logging
from typing import List

from fastapi import APIRouter, Depends

from bookrover.config import Settings
from bookrover.dependencies import get_dynamodb_resource, get_settings
from bookrover.models.lookup import BookStoreSummary, GroupLeaderLookupResponse
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lookup", tags=["Lookup"])


# ------------------------------------------------------------------
# Dependency provider
# ------------------------------------------------------------------


def get_lookup_repos(
    dynamodb=Depends(get_dynamodb_resource),
    settings: Settings = Depends(get_settings),
):
    """Build and return the two repositories needed for lookup.

    Args:
        dynamodb: Injected boto3 DynamoDB resource.
        settings: Injected application settings.

    Returns:
        Tuple of (DynamoDBGroupLeaderRepository, DynamoDBBookstoreRepository).
    """
    group_leaders_table = dynamodb.Table(settings.get_table_name("group-leaders"))
    sellers_table = dynamodb.Table(settings.get_table_name("sellers"))
    bookstores_table = dynamodb.Table(settings.get_table_name("bookstores"))

    group_leader_repo = DynamoDBGroupLeaderRepository(
        table=group_leaders_table,
        sellers_table=sellers_table,
    )
    bookstore_repo = DynamoDBBookstoreRepository(table=bookstores_table)
    return group_leader_repo, bookstore_repo


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get(
    "/group-leaders",
    response_model=List[GroupLeaderLookupResponse],
    status_code=200,
    summary="List group leaders with their bookstores",
    description=(
        "Returns all group leaders, each with the bookstores they manage. "
        "Used to populate the Seller registration dropdown: "
        "'Group Leader Name — Bookstore Name' → (group_leader_id, bookstore_id)."
    ),
)
async def list_group_leaders_for_lookup(
    repos=Depends(get_lookup_repos),
) -> List[GroupLeaderLookupResponse]:
    """Return all group leaders with their linked bookstores.

    Fetches all bookstores once as a lookup dict, then maps each group
    leader's bookstore_ids to BookStoreSummary objects.

    Args:
        repos: Injected (group_leader_repo, bookstore_repo) tuple.

    Returns:
        List of GroupLeaderLookupResponse objects.
    """
    group_leader_repo, bookstore_repo = repos

    all_bookstores = bookstore_repo.list_all()
    bookstore_map: dict = {b["bookstore_id"]: b["store_name"] for b in all_bookstores}

    all_leaders = group_leader_repo.list_all()
    logger.info("Lookup: fetched group leaders for registration dropdown")

    result = []
    for leader in all_leaders:
        bookstores = [
            BookStoreSummary(bookstore_id=bid, store_name=bookstore_map[bid])
            for bid in leader.get("bookstore_ids", [])
            if bid in bookstore_map
        ]
        result.append(
            GroupLeaderLookupResponse(
                group_leader_id=leader["group_leader_id"],
                name=leader["name"],
                bookstores=bookstores,
            )
        )
    return result
