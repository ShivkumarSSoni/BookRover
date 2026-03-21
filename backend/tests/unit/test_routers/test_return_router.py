"""Unit tests for the Returns router.

Verifies HTTP behaviour using FastAPI TestClient with a mocked
AbstractReturnService injected via Depends(). No repository, no DynamoDB,
no moto required.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bookrover.exceptions.not_found import BookStoreNotFoundError, SellerNotFoundError
from bookrover.interfaces.abstract_return_service import AbstractReturnService
from bookrover.main import create_app
from bookrover.models.return_models import (
    ReturnItemResponse,
    ReturnResponse,
    ReturnSummaryBook,
    ReturnSummaryBookstoreInfo,
    ReturnSummaryResponse,
)
from bookrover.routers.returns import get_return_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service():
    """Mock AbstractReturnService."""
    return MagicMock(spec=AbstractReturnService)


@pytest.fixture
def client(mock_service):
    """TestClient with the mock service injected via dependency override."""
    app = create_app()
    app.dependency_overrides[get_return_service] = lambda: mock_service
    return TestClient(app)


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

BOOKSTORE_INFO = ReturnSummaryBookstoreInfo(
    bookstore_id="bs-001",
    store_name="Sri Lakshmi Books",
    owner_name="Lakshmi Devi",
    address="12 MG Road, Chennai",
    phone_number="+914423456789",
)

SUMMARY_BOOK = ReturnSummaryBook(
    book_id="book-001",
    book_name="Thirukkural",
    language="Tamil",
    quantity_to_return=8,
    cost_per_book=50.0,
    total_cost=400.0,
)

SUMMARY_RESPONSE = ReturnSummaryResponse(
    seller_id="seller-001",
    bookstore=BOOKSTORE_INFO,
    books_to_return=[SUMMARY_BOOK],
    total_books_to_return=8,
    total_cost_of_unsold_books=400.0,
    total_money_collected_from_sales=225.0,
)

RETURN_ITEM = ReturnItemResponse(
    book_id="book-001",
    book_name="Thirukkural",
    language="Tamil",
    quantity_returned=8,
    cost_per_book=50.0,
    total_cost=400.0,
)

RETURN_RESPONSE = ReturnResponse(
    return_id="ret-001",
    seller_id="seller-001",
    bookstore_id="bs-001",
    return_items=[RETURN_ITEM],
    total_books_returned=8,
    total_money_returned=225.0,
    status="completed",
    return_date="2026-03-21T18:00:00Z",
)

SELLER_ID = "seller-001"


# ---------------------------------------------------------------------------
# GET /sellers/{seller_id}/return-summary
# ---------------------------------------------------------------------------


def test_get_return_summary_returns_200_with_all_fields(client, mock_service):
    """GET /sellers/{id}/return-summary should return 200 with full payload."""
    mock_service.get_return_summary.return_value = SUMMARY_RESPONSE

    response = client.get(f"/sellers/{SELLER_ID}/return-summary")

    assert response.status_code == 200
    data = response.json()
    assert data["seller_id"] == SELLER_ID
    assert data["bookstore"]["store_name"] == "Sri Lakshmi Books"
    assert data["bookstore"]["owner_name"] == "Lakshmi Devi"
    assert len(data["books_to_return"]) == 1
    assert data["total_books_to_return"] == 8
    assert data["total_cost_of_unsold_books"] == 400.0
    assert data["total_money_collected_from_sales"] == 225.0


def test_get_return_summary_delegates_seller_id(client, mock_service):
    """GET /sellers/{id}/return-summary passes the correct seller_id to the service."""
    mock_service.get_return_summary.return_value = SUMMARY_RESPONSE

    client.get(f"/sellers/{SELLER_ID}/return-summary")

    mock_service.get_return_summary.assert_called_once_with(SELLER_ID)


def test_get_return_summary_returns_404_for_unknown_seller(client, mock_service):
    """GET /sellers/{id}/return-summary returns 404 when seller does not exist."""
    mock_service.get_return_summary.side_effect = SellerNotFoundError("unknown-seller")

    response = client.get("/sellers/unknown-seller/return-summary")

    assert response.status_code == 404
    assert "unknown-seller" in response.json()["detail"]


def test_get_return_summary_returns_404_when_bookstore_not_found(client, mock_service):
    """GET /sellers/{id}/return-summary returns 404 when bookstore is missing."""
    mock_service.get_return_summary.side_effect = BookStoreNotFoundError("bs-missing")

    response = client.get(f"/sellers/{SELLER_ID}/return-summary")

    assert response.status_code == 404
    assert "bs-missing" in response.json()["detail"]


def test_get_return_summary_books_to_return_row_shape(client, mock_service):
    """Books-to-return rows include book_id, book_name, language, qty, cost, total."""
    mock_service.get_return_summary.return_value = SUMMARY_RESPONSE

    response = client.get(f"/sellers/{SELLER_ID}/return-summary")

    book = response.json()["books_to_return"][0]
    assert book["book_id"] == "book-001"
    assert book["book_name"] == "Thirukkural"
    assert book["language"] == "Tamil"
    assert book["quantity_to_return"] == 8
    assert book["cost_per_book"] == 50.0
    assert book["total_cost"] == 400.0


# ---------------------------------------------------------------------------
# POST /sellers/{seller_id}/returns
# ---------------------------------------------------------------------------


def test_submit_return_returns_201_with_return_id(client, mock_service):
    """POST /sellers/{id}/returns should return 201 with the return record."""
    mock_service.submit_return.return_value = RETURN_RESPONSE

    response = client.post(f"/sellers/{SELLER_ID}/returns", json={})

    assert response.status_code == 201
    data = response.json()
    assert data["return_id"] == "ret-001"
    assert data["seller_id"] == SELLER_ID
    assert data["bookstore_id"] == "bs-001"
    assert data["status"] == "completed"
    assert data["total_books_returned"] == 8
    assert data["total_money_returned"] == 225.0


def test_submit_return_passes_notes_to_service(client, mock_service):
    """POST /sellers/{id}/returns passes optional notes to the service."""
    mock_service.submit_return.return_value = RETURN_RESPONSE

    client.post(f"/sellers/{SELLER_ID}/returns", json={"notes": "Good condition"})

    mock_service.submit_return.assert_called_once_with(SELLER_ID, "Good condition")


def test_submit_return_passes_none_notes_when_omitted(client, mock_service):
    """POST /sellers/{id}/returns passes None for notes when omitted."""
    mock_service.submit_return.return_value = RETURN_RESPONSE

    client.post(f"/sellers/{SELLER_ID}/returns", json={})

    mock_service.submit_return.assert_called_once_with(SELLER_ID, None)


def test_submit_return_returns_404_for_unknown_seller(client, mock_service):
    """POST /sellers/{id}/returns returns 404 when seller does not exist."""
    mock_service.submit_return.side_effect = SellerNotFoundError("unknown-seller")

    response = client.post("/sellers/unknown-seller/returns", json={})

    assert response.status_code == 404
    assert "unknown-seller" in response.json()["detail"]


def test_submit_return_return_items_row_shape(client, mock_service):
    """POST /sellers/{id}/returns — return_items include correct fields."""
    mock_service.submit_return.return_value = RETURN_RESPONSE

    response = client.post(f"/sellers/{SELLER_ID}/returns", json={})

    item = response.json()["return_items"][0]
    assert item["book_id"] == "book-001"
    assert item["quantity_returned"] == 8
    assert item["cost_per_book"] == 50.0
    assert item["total_cost"] == 400.0
