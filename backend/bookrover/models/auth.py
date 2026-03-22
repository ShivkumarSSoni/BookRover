"""Pydantic DTOs for the Auth feature.

MeResponse: returned by GET /me — carries the caller's resolved roles and IDs.
MockTokenRequest: the body accepted by POST /dev/mock-token (dev-only).
MockTokenResponse: returned by POST /dev/mock-token.
"""

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class MeResponse(BaseModel):
    """Response from GET /me — the caller's identity and resolved BookRover roles.

    Attributes:
        email: The authenticated user's email address.
        roles: List of BookRover roles assigned to this user.
                Possible values: 'admin', 'group_leader', 'seller'.
                Empty list means the user is new and should complete registration.
        seller_id: UUID of the seller profile, if the user is a seller.
        group_leader_id: UUID of the group leader profile, if the user is a group leader.
    """

    email: str
    roles: List[str]
    seller_id: Optional[str] = None
    group_leader_id: Optional[str] = None


class MockTokenRequest(BaseModel):
    """Request body for POST /dev/mock-token (development only).

    Attributes:
        email: Any email address to issue a dev token for.
    """

    email: EmailStr = Field(..., description="Email address to issue a dev token for.")


class MockTokenResponse(BaseModel):
    """Response from POST /dev/mock-token.

    Attributes:
        token: Opaque dev token. Pass as Authorization: Bearer <token>.
        email: The email address this token represents.
    """

    token: str
    email: str
