"""Pydantic DTOs for public lookup endpoints.

These models serve the Seller registration dropdown:
  GET /group-leaders  → list of group leaders with their bookstores
  GET /bookstores     → list of bookstores (id + name only)
"""

from typing import List

from pydantic import BaseModel


class BookStoreSummary(BaseModel):
    """Minimal bookstore info for the registration dropdown."""

    bookstore_id: str
    store_name: str


class GroupLeaderLookupResponse(BaseModel):
    """Group leader with their linked bookstores — used for the registration dropdown.

    Display format in UI: "{name} — {store_name}".
    Each combination maps to a unique (group_leader_id, bookstore_id) pair.
    """

    group_leader_id: str
    name: str
    bookstores: List[BookStoreSummary]
