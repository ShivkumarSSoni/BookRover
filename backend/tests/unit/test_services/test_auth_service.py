"""Unit tests for AuthService.

AuthService is tested with mocked repository ABCs — no moto, no DynamoDB.
"""

from unittest.mock import MagicMock

import pytest

from bookrover.interfaces.abstract_group_leader_repository import AbstractGroupLeaderRepository
from bookrover.interfaces.abstract_seller_repository import AbstractSellerRepository
from bookrover.services.auth_service import AuthService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seller_repo():
    return MagicMock(spec=AbstractSellerRepository)


@pytest.fixture
def group_leader_repo():
    return MagicMock(spec=AbstractGroupLeaderRepository)


ADMIN_EMAIL = "admin@bookrover.com"
GL_EMAIL = "ravi@bookrover.com"
SELLER_EMAIL = "anand@bookrover.com"
BOTH_EMAIL = "both@bookrover.com"
NEW_USER_EMAIL = "newuser@bookrover.com"

GL_ITEM = {"group_leader_id": "gl-001", "name": "Ravi Kumar", "email": GL_EMAIL}
SELLER_ITEM = {"seller_id": "sel-001", "first_name": "Anand", "email": SELLER_EMAIL}
BOTH_GL_ITEM = {"group_leader_id": "gl-002", "email": BOTH_EMAIL}
BOTH_SELLER_ITEM = {"seller_id": "sel-002", "email": BOTH_EMAIL}


def make_service(seller_repo, group_leader_repo, admin_emails=None):
    return AuthService(
        seller_repository=seller_repo,
        group_leader_repository=group_leader_repo,
        admin_emails=admin_emails or [ADMIN_EMAIL],
    )


# ---------------------------------------------------------------------------
# Admin role
# ---------------------------------------------------------------------------


def test_get_me_returns_admin_role_for_admin_email(seller_repo, group_leader_repo):
    service = make_service(seller_repo, group_leader_repo)
    result = service.get_me(ADMIN_EMAIL)

    assert result.roles == ["admin"]
    assert result.seller_id is None
    assert result.group_leader_id is None
    assert result.email == ADMIN_EMAIL


def test_get_me_admin_skips_dynamodb_lookup(seller_repo, group_leader_repo):
    service = make_service(seller_repo, group_leader_repo)
    service.get_me(ADMIN_EMAIL)

    seller_repo.get_by_email.assert_not_called()
    group_leader_repo.get_by_email.assert_not_called()


def test_get_me_admin_email_comparison_is_case_insensitive(seller_repo, group_leader_repo):
    service = make_service(seller_repo, group_leader_repo, admin_emails=["Admin@BookRover.COM"])
    result = service.get_me("admin@bookrover.com")

    assert "admin" in result.roles


# ---------------------------------------------------------------------------
# Group leader role
# ---------------------------------------------------------------------------


def test_get_me_returns_group_leader_role(seller_repo, group_leader_repo):
    group_leader_repo.get_by_email.return_value = GL_ITEM
    seller_repo.get_by_email.return_value = None
    service = make_service(seller_repo, group_leader_repo)

    result = service.get_me(GL_EMAIL)

    assert result.roles == ["group_leader"]
    assert result.group_leader_id == "gl-001"
    assert result.seller_id is None
    assert result.email == GL_EMAIL


# ---------------------------------------------------------------------------
# Seller role
# ---------------------------------------------------------------------------


def test_get_me_returns_seller_role(seller_repo, group_leader_repo):
    group_leader_repo.get_by_email.return_value = None
    seller_repo.get_by_email.return_value = SELLER_ITEM
    service = make_service(seller_repo, group_leader_repo)

    result = service.get_me(SELLER_EMAIL)

    assert result.roles == ["seller"]
    assert result.seller_id == "sel-001"
    assert result.group_leader_id is None
    assert result.email == SELLER_EMAIL


# ---------------------------------------------------------------------------
# Multi-role: group_leader + seller
# ---------------------------------------------------------------------------


def test_get_me_returns_both_roles_when_user_is_in_both_tables(seller_repo, group_leader_repo):
    group_leader_repo.get_by_email.return_value = BOTH_GL_ITEM
    seller_repo.get_by_email.return_value = BOTH_SELLER_ITEM
    service = make_service(seller_repo, group_leader_repo)

    result = service.get_me(BOTH_EMAIL)

    assert "group_leader" in result.roles
    assert "seller" in result.roles
    assert result.group_leader_id == "gl-002"
    assert result.seller_id == "sel-002"


# ---------------------------------------------------------------------------
# New user — no roles
# ---------------------------------------------------------------------------


def test_get_me_returns_empty_roles_for_new_user(seller_repo, group_leader_repo):
    group_leader_repo.get_by_email.return_value = None
    seller_repo.get_by_email.return_value = None
    service = make_service(seller_repo, group_leader_repo)

    result = service.get_me(NEW_USER_EMAIL)

    assert result.roles == []
    assert result.seller_id is None
    assert result.group_leader_id is None
    assert result.email == NEW_USER_EMAIL
