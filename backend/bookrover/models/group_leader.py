"""Pydantic DTOs for the GroupLeader entity.

Contains request and response models used by the Admin router
for GroupLeader create, update, and read operations.
"""

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class GroupLeaderCreate(BaseModel):
    """Request body for creating a new GroupLeader."""

    name: str = Field(..., min_length=1, max_length=100, description="Full name of the group leader")
    email: EmailStr = Field(..., description="Gmail address — must be unique")
    bookstore_ids: List[str] = Field(..., min_length=1, description="List of associated bookstore UUIDs")


class GroupLeaderUpdate(BaseModel):
    """Request body for updating an existing GroupLeader.

    All fields are optional — only supplied fields are updated.
    Email is intentionally excluded; it cannot be changed after creation.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    bookstore_ids: Optional[List[str]] = Field(None, min_length=1)


class GroupLeaderResponse(BaseModel):
    """Response model for a GroupLeader — returned by all read and write operations."""

    group_leader_id: str
    name: str
    email: str
    bookstore_ids: List[str]
    created_at: str
    updated_at: str
