"""Integration tests for Admin endpoints.

Tests the full HTTP → Service → Repository → DynamoDB round trip
using moto to mock AWS. Real repositories and a real AdminService are
wired together; only DynamoDB is replaced by moto's in-memory store.
"""

import pytest
from fastapi.testclient import TestClient

from bookrover.main import create_app
from bookrover.repositories.bookstore_repository import DynamoDBBookstoreRepository
from bookrover.repositories.group_leader_repository import DynamoDBGroupLeaderRepository
from bookrover.routers.admin import get_admin_service
from bookrover.services.admin_service import AdminService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def integration_client(dynamodb_tables):
    """TestClient wired with real service + real repositories against moto DynamoDB.

    The `dynamodb_tables` fixture (from conftest.py) provides a moto-backed
    boto3 resource with all 7 tables pre-created.
    """
    bookstore_table = dynamodb_tables.Table("bookrover-bookstores-test")
    group_leaders_table = dynamodb_tables.Table("bookrover-group-leaders-test")
    sellers_table = dynamodb_tables.Table("bookrover-sellers-test")

    bookstore_repo = DynamoDBBookstoreRepository(table=bookstore_table)
    group_leader_repo = DynamoDBGroupLeaderRepository(
        table=group_leaders_table,
        sellers_table=sellers_table,
    )
    real_service = AdminService(
        bookstore_repository=bookstore_repo,
        group_leader_repository=group_leader_repo,
    )

    app = create_app()
    app.dependency_overrides[get_admin_service] = lambda: real_service
    return TestClient(app)


# ---------------------------------------------------------------------------
# BookStore integration tests
# ---------------------------------------------------------------------------

BOOKSTORE_PAYLOAD = {
    "store_name": "Sri Lakshmi Books",
    "owner_name": "Lakshmi Devi",
    "address": "12 MG Road, Chennai, TN 600001",
    "phone_number": "+914423456789",
}

GROUP_LEADER_PAYLOAD = {
    "name": "Ravi Kumar",
    "email": "ravi@gmail.com",
    "bookstore_ids": [],  # will be filled in after bookstore is created
}


def test_create_and_list_bookstores(integration_client):
    """Creating a bookstore and listing it should return the same data."""
    create_response = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["store_name"] == "Sri Lakshmi Books"
    bookstore_id = created["bookstore_id"]

    list_response = integration_client.get("/admin/bookstores")
    assert list_response.status_code == 200
    bookstores = list_response.json()
    ids = [b["bookstore_id"] for b in bookstores]
    assert bookstore_id in ids


def test_create_bookstore_stores_all_fields(integration_client):
    """All submitted fields should be persisted and returned on create."""
    response = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["store_name"] == BOOKSTORE_PAYLOAD["store_name"]
    assert data["owner_name"] == BOOKSTORE_PAYLOAD["owner_name"]
    assert data["address"] == BOOKSTORE_PAYLOAD["address"]
    assert data["phone_number"] == BOOKSTORE_PAYLOAD["phone_number"]
    assert "bookstore_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_update_bookstore_persists_change(integration_client):
    """An update should persist only the changed field to DynamoDB."""
    create_res = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    bookstore_id = create_res.json()["bookstore_id"]

    update_res = integration_client.put(
        f"/admin/bookstores/{bookstore_id}",
        json={"owner_name": "New Owner"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["owner_name"] == "New Owner"
    assert update_res.json()["store_name"] == "Sri Lakshmi Books"


def test_update_bookstore_returns_404_for_unknown_id(integration_client):
    """Updating a non-existent bookstore should return 404."""
    response = integration_client.put(
        "/admin/bookstores/nonexistent-id",
        json={"owner_name": "Ghost"},
    )
    assert response.status_code == 404


def test_delete_bookstore_removes_record(integration_client):
    """Deleting a bookstore should make it disappear from the list."""
    create_res = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    bookstore_id = create_res.json()["bookstore_id"]

    delete_res = integration_client.delete(f"/admin/bookstores/{bookstore_id}")
    assert delete_res.status_code == 204

    list_res = integration_client.get("/admin/bookstores")
    ids = [b["bookstore_id"] for b in list_res.json()]
    assert bookstore_id not in ids


def test_delete_bookstore_returns_404_for_unknown_id(integration_client):
    """Deleting a non-existent bookstore should return 404."""
    response = integration_client.delete("/admin/bookstores/nonexistent-id")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GroupLeader integration tests
# ---------------------------------------------------------------------------


def test_create_and_list_group_leaders(integration_client):
    """Creating a group leader and listing should return the same data."""
    create_res = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    bookstore_id = create_res.json()["bookstore_id"]

    gl_payload = {**GROUP_LEADER_PAYLOAD, "bookstore_ids": [bookstore_id]}
    create_gl_res = integration_client.post("/admin/group-leaders", json=gl_payload)
    assert create_gl_res.status_code == 201
    gl = create_gl_res.json()
    assert gl["name"] == "Ravi Kumar"
    assert bookstore_id in gl["bookstore_ids"]

    list_res = integration_client.get("/admin/group-leaders")
    assert list_res.status_code == 200
    ids = [g["group_leader_id"] for g in list_res.json()]
    assert gl["group_leader_id"] in ids


def test_create_group_leader_rejects_duplicate_email(integration_client):
    """Creating two group leaders with the same email should return 409 on second attempt."""
    create_res = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    bookstore_id = create_res.json()["bookstore_id"]
    gl_payload = {**GROUP_LEADER_PAYLOAD, "bookstore_ids": [bookstore_id]}

    first_res = integration_client.post("/admin/group-leaders", json=gl_payload)
    assert first_res.status_code == 201

    second_res = integration_client.post("/admin/group-leaders", json=gl_payload)
    assert second_res.status_code == 409
    assert "ravi@gmail.com" in second_res.json()["detail"]


def test_update_group_leader_persists_change(integration_client):
    """Updating a group leader's name should persist to DynamoDB."""
    create_res = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    bookstore_id = create_res.json()["bookstore_id"]
    gl_payload = {**GROUP_LEADER_PAYLOAD, "bookstore_ids": [bookstore_id]}

    gl_res = integration_client.post("/admin/group-leaders", json=gl_payload)
    gl_id = gl_res.json()["group_leader_id"]

    update_res = integration_client.put(f"/admin/group-leaders/{gl_id}", json={"name": "Ravi K Updated"})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Ravi K Updated"
    assert update_res.json()["email"] == "ravi@gmail.com"


def test_delete_group_leader_removes_record(integration_client):
    """Deleting a group leader should remove them from the list."""
    create_res = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    bookstore_id = create_res.json()["bookstore_id"]
    gl_payload = {**GROUP_LEADER_PAYLOAD, "bookstore_ids": [bookstore_id]}

    gl_res = integration_client.post("/admin/group-leaders", json=gl_payload)
    gl_id = gl_res.json()["group_leader_id"]

    delete_res = integration_client.delete(f"/admin/group-leaders/{gl_id}")
    assert delete_res.status_code == 204

    list_res = integration_client.get("/admin/group-leaders")
    ids = [g["group_leader_id"] for g in list_res.json()]
    assert gl_id not in ids


def test_delete_group_leader_with_active_sellers_returns_409(integration_client, dynamodb_tables):
    """Deleting a group leader who has active sellers should return 409."""
    create_res = integration_client.post("/admin/bookstores", json=BOOKSTORE_PAYLOAD)
    bookstore_id = create_res.json()["bookstore_id"]
    gl_payload = {**GROUP_LEADER_PAYLOAD, "bookstore_ids": [bookstore_id]}

    gl_res = integration_client.post("/admin/group-leaders", json=gl_payload)
    gl_id = gl_res.json()["group_leader_id"]

    # Directly seed a seller into the sellers table pointing to this group leader
    sellers_table = dynamodb_tables.Table("bookrover-sellers-test")
    sellers_table.put_item(Item={
        "seller_id": "seller-001",
        "group_leader_id": gl_id,
        "bookstore_id": bookstore_id,
        "status": "active",
        "first_name": "Test",
        "last_name": "Seller",
        "email": "seller@gmail.com",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    })

    response = integration_client.delete(f"/admin/group-leaders/{gl_id}")
    assert response.status_code == 409
    assert str(gl_id) in response.json()["detail"]
