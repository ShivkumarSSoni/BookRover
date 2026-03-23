"""Unit tests for the Sales router.

Verifies HTTP behaviour using FastAPI TestClient with a mocked
AbstractSaleService injected via Depends(). No repository, no DynamoDB,
no moto required.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.exceptions.bad_request import InsufficientInventoryError
from bookrover.exceptions.conflict import SellerPendingReturnError
from bookrover.exceptions.not_found import BookNotFoundError, SaleNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_sale_service import AbstractSaleService
from bookrover.main import create_app
from bookrover.models.auth import MeResponse
from bookrover.models.sale import SaleItemResponse, SaleResponse
from bookrover.routers.auth import get_current_user
from bookrover.routers.sales import get_sale_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


SELLER_ME = MeResponse(email="seller@example.com", roles=["seller"], seller_id="sel-001")


@pytest.fixture
def mock_service():
    """Mock AbstractSaleService."""
    return MagicMock(spec=AbstractSaleService)


@pytest.fixture
def client(mock_service):
    """TestClient with mock service and seller sel-001 injected as current user."""
    app = create_app()
    app.dependency_overrides[get_sale_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: SELLER_ME
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SALE_ITEM_RESPONSE = SaleItemResponse(
    book_id="book-001",
    book_name="Thirukkural",
    language="Tamil",
    quantity_sold=2,
    selling_price=75.0,
    subtotal=150.0,
)

SALE_RESPONSE = SaleResponse(
    sale_id="sale-001",
    seller_id="sel-001",
    bookstore_id="bs-001",
    buyer_first_name="Ravi",
    buyer_last_name="Kumar",
    buyer_country_code="+91",
    buyer_phone="9876543210",
    sale_items=[SALE_ITEM_RESPONSE],
    total_books_sold=2,
    total_amount_collected=150.0,
    sale_date="2026-01-01T00:00:00Z",
    created_at="2026-01-01T00:00:00Z",
)

CREATE_SALE_PAYLOAD = {
    "buyer_first_name": "Ravi",
    "buyer_last_name": "Kumar",
    "buyer_country_code": "+91",
    "buyer_phone": "9876543210",
    "items": [{"book_id": "book-001", "quantity_sold": 2}],
}


# ---------------------------------------------------------------------------
# POST /sellers/{seller_id}/sales
# ---------------------------------------------------------------------------


def test_create_sale_returns_201_for_valid_input(client, mock_service):
    """POST /sellers/{id}/sales should return 201 with the created sale."""
    mock_service.create_sale.return_value = SALE_RESPONSE

    response = client.post("/sellers/sel-001/sales", json=CREATE_SALE_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["sale_id"] == "sale-001"
    assert data["total_books_sold"] == 2
    assert data["total_amount_collected"] == 150.0


def test_create_sale_returns_404_for_unknown_seller(client, mock_service):
    """POST /sellers/{id}/sales should return 404 if seller not found."""
    mock_service.create_sale.side_effect = SellerNotFoundError("sel-001")

    response = client.post("/sellers/sel-001/sales", json=CREATE_SALE_PAYLOAD)

    assert response.status_code == 404
    assert "sel-001" in response.json()["detail"]


def test_create_sale_returns_404_for_unknown_book(client, mock_service):
    """POST /sellers/{id}/sales should return 404 if a book_id does not exist."""
    mock_service.create_sale.side_effect = BookNotFoundError("bad-book")

    response = client.post("/sellers/sel-001/sales", json=CREATE_SALE_PAYLOAD)

    assert response.status_code == 404
    assert "bad-book" in response.json()["detail"]


def test_create_sale_returns_400_for_insufficient_inventory(client, mock_service):
    """POST /sellers/{id}/sales should return 400 if stock is insufficient."""
    mock_service.create_sale.side_effect = InsufficientInventoryError("book-001", 5, 2)

    response = client.post("/sellers/sel-001/sales", json=CREATE_SALE_PAYLOAD)

    assert response.status_code == 400
    assert "book-001" in response.json()["detail"]


def test_create_sale_returns_409_for_pending_return_seller(client, mock_service):
    """POST /sellers/{id}/sales should return 409 if seller is pending_return."""
    mock_service.create_sale.side_effect = SellerPendingReturnError("sel-001")

    response = client.post("/sellers/sel-001/sales", json=CREATE_SALE_PAYLOAD)

    assert response.status_code == 409
    assert "sel-001" in response.json()["detail"]


def test_create_sale_returns_422_for_missing_items(client, mock_service):
    """POST /sellers/{id}/sales should return 422 if items list is missing."""
    payload = {k: v for k, v in CREATE_SALE_PAYLOAD.items() if k != "items"}

    response = client.post("/sellers/sel-001/sales", json=payload)

    assert response.status_code == 422


def test_create_sale_returns_422_for_empty_items_list(client, mock_service):
    """POST /sellers/{id}/sales should return 422 if items list is empty."""
    response = client.post("/sellers/sel-001/sales", json={**CREATE_SALE_PAYLOAD, "items": []})

    assert response.status_code == 422


def test_create_sale_returns_422_for_invalid_phone(client, mock_service):
    """POST /sellers/{id}/sales should return 422 if buyer_phone contains non-digits."""
    response = client.post(
        "/sellers/sel-001/sales",
        json={**CREATE_SALE_PAYLOAD, "buyer_phone": "abc-xyz"},
    )

    assert response.status_code == 422


def test_create_sale_returns_422_for_zero_quantity(client, mock_service):
    """POST /sellers/{id}/sales should return 422 if any quantity_sold is 0."""
    payload = {**CREATE_SALE_PAYLOAD, "items": [{"book_id": "book-001", "quantity_sold": 0}]}

    response = client.post("/sellers/sel-001/sales", json=payload)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}/sales
# ---------------------------------------------------------------------------


def test_list_sales_returns_200_with_sales(client, mock_service):
    """GET /sellers/{id}/sales should return 200 with list of sales."""
    mock_service.list_sales.return_value = [SALE_RESPONSE]

    response = client.get("/sellers/sel-001/sales")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["sale_id"] == "sale-001"


def test_list_sales_returns_200_with_empty_list(client, mock_service):
    """GET /sellers/{id}/sales should return 200 with empty list when no sales exist."""
    mock_service.list_sales.return_value = []

    response = client.get("/sellers/sel-001/sales")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}/sales/{sale_id}
# ---------------------------------------------------------------------------


def test_get_sale_returns_200_for_valid_ids(client, mock_service):
    """GET /sellers/{id}/sales/{sale_id} should return 200 with sale detail."""
    mock_service.get_sale.return_value = SALE_RESPONSE

    response = client.get("/sellers/sel-001/sales/sale-001")

    assert response.status_code == 200
    data = response.json()
    assert data["sale_id"] == "sale-001"
    assert data["buyer_first_name"] == "Ravi"
    assert len(data["sale_items"]) == 1


def test_get_sale_returns_404_for_missing_sale(client, mock_service):
    """GET /sellers/{id}/sales/{sale_id} should return 404 if sale not found."""
    mock_service.get_sale.side_effect = SaleNotFoundError("no-sale")

    response = client.get("/sellers/sel-001/sales/no-sale")

    assert response.status_code == 404
    assert "no-sale" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Auth enforcement tests
# ---------------------------------------------------------------------------


def test_sales_endpoint_returns_401_without_auth():
    """Sales endpoints must return 401 when no Authorization header is present."""
    app = create_app()
    c = TestClient(app)
    response = c.get("/sellers/sel-001/sales")
    assert response.status_code == 401


def test_sales_endpoint_returns_403_for_non_seller_role():
    """Sales endpoints must return 403 for a GL or admin caller (not a seller)."""
    gl_me = MeResponse(email="gl@example.com", roles=["group_leader"], group_leader_id="gl-001")
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: gl_me
    c = TestClient(app)
    response = c.get("/sellers/sel-001/sales")
    assert response.status_code == 403


def test_sales_endpoint_returns_403_for_wrong_seller_id(client, mock_service):
    """Sales endpoints must return 403 when the seller_id path param belongs to another seller."""
    response = client.get("/sellers/sel-DIFFERENT/sales")
    assert response.status_code == 403


def test_create_sale_returns_403_for_wrong_seller_id(client, mock_service):
    """POST sales must return 403 when the seller_id path param belongs to another seller."""
    response = client.post("/sellers/sel-DIFFERENT/sales", json=CREATE_SALE_PAYLOAD)
    assert response.status_code == 403
