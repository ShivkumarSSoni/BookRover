# BookRover — API Specification

## Base URL

- **Development (local)**: `http://localhost:8000`
- **Production (AWS)**: `https://api.<your-domain>.com` (via API Gateway + Lambda)

## General Conventions

- All requests and responses use `Content-Type: application/json`.
- All IDs are UUID v4 strings.
- All timestamps are ISO 8601 UTC strings.
- Error responses always follow: `{"detail": "human-readable message"}`
- Decimal values (prices, amounts) are represented as numbers with 2 decimal places.
- Authentication: all endpoints will require a Bearer token (via Cognito) — deferred. For now, endpoints are open for development.

---

## 1. Admin Endpoints

### 1.1 Create Group Leader
```
POST /admin/group-leaders
```
**Request Body:**
```json
{
  "name": "Ravi Kumar",
  "email": "ravi@gmail.com",
  "bookstore_ids": ["<bookstore_uuid>"]
}
```
**Response `201 Created`:**
```json
{
  "group_leader_id": "<uuid>",
  "name": "Ravi Kumar",
  "email": "ravi@gmail.com",
  "bookstore_ids": ["<bookstore_uuid>"],
  "created_at": "2026-03-21T10:00:00Z"
}
```
**Errors:**
- `409 Conflict` — email already exists.
- `422 Unprocessable Entity` — validation failure.

---

### 1.2 List Group Leaders
```
GET /admin/group-leaders
```
**Response `200 OK`:**
```json
[
  {
    "group_leader_id": "<uuid>",
    "name": "Ravi Kumar",
    "email": "ravi@gmail.com",
    "bookstore_ids": ["<bookstore_uuid>"],
    "created_at": "2026-03-21T10:00:00Z"
  }
]
```

---

### 1.3 Update Group Leader
```
PUT /admin/group-leaders/{group_leader_id}
```
**Request Body** (any combination of fields):
```json
{
  "name": "Ravi Kumar Updated",
  "bookstore_ids": ["<bookstore_uuid_1>", "<bookstore_uuid_2>"]
}
```
**Response `200 OK`:** Updated group leader object.  
**Errors:** `404 Not Found`, `422 Unprocessable Entity`

---

### 1.4 Delete Group Leader
```
DELETE /admin/group-leaders/{group_leader_id}
```
**Response `204 No Content`**  
**Errors:**
- `404 Not Found`
- `409 Conflict` — group leader has active sellers assigned; cannot delete.

---

### 1.5 Create BookStore
```
POST /admin/bookstores
```
**Request Body:**
```json
{
  "store_name": "Sri Lakshmi Books",
  "owner_name": "Lakshmi Devi",
  "address": "12 MG Road, Chennai, TN 600001",
  "phone_number": "+914423456789"
}
```
**Response `201 Created`:**
```json
{
  "bookstore_id": "<uuid>",
  "store_name": "Sri Lakshmi Books",
  "owner_name": "Lakshmi Devi",
  "address": "12 MG Road, Chennai, TN 600001",
  "phone_number": "+914423456789",
  "created_at": "2026-03-21T10:00:00Z"
}
```
**Errors:** `422 Unprocessable Entity`

---

### 1.6 List BookStores
```
GET /admin/bookstores
```
**Response `200 OK`:** Array of bookstore objects.

---

### 1.7 Update BookStore
```
PUT /admin/bookstores/{bookstore_id}
```
**Request Body** (any combination of fields):
```json
{
  "owner_name": "New Owner Name",
  "phone_number": "+919876543210"
}
```
**Response `200 OK`:** Updated bookstore object.  
**Errors:** `404 Not Found`, `422 Unprocessable Entity`

---

### 1.8 Delete BookStore
```
DELETE /admin/bookstores/{bookstore_id}
```
**Response `204 No Content`**  
**Errors:**
- `404 Not Found`
- `409 Conflict` — bookstore has active inventory or pending returns.

---

## 2. Lookup Endpoints (used by Seller registration dropdowns)

### 2.1 List All BookStores (public)
```
GET /bookstores
```
**Response `200 OK`:** Array of `{ bookstore_id, store_name, owner_name }` objects.

---

### 2.2 List All Group Leaders with Their BookStores (public)
```
GET /group-leaders
```
**Response `200 OK`:**
```json
[
  {
    "group_leader_id": "<uuid>",
    "name": "Ravi Kumar",
    "bookstores": [
      { "bookstore_id": "<uuid>", "store_name": "Sri Lakshmi Books" }
    ]
  }
]
```
This provides the data for the Seller registration dropdown: `"Ravi Kumar — Sri Lakshmi Books"`.

---

## 3. Seller Endpoints

### 3.1 Register Seller
```
POST /sellers
```
**Request Body:**
```json
{
  "first_name": "Anand",
  "last_name": "Raj",
  "email": "anand@gmail.com",
  "group_leader_id": "<uuid>",
  "bookstore_id": "<uuid>"
}
```
**Response `201 Created`:**
```json
{
  "seller_id": "<uuid>",
  "first_name": "Anand",
  "last_name": "Raj",
  "email": "anand@gmail.com",
  "group_leader_id": "<uuid>",
  "bookstore_id": "<uuid>",
  "status": "active",
  "created_at": "2026-03-21T10:00:00Z"
}
```
**Errors:**
- `409 Conflict` — email already registered.
- `404 Not Found` — group_leader_id or bookstore_id does not exist.
- `422 Unprocessable Entity` — validation failure.

---

### 3.2 Get Seller Profile
```
GET /sellers/{seller_id}
```
**Response `200 OK`:** Full seller object including `status`.  
**Errors:** `404 Not Found`

---

### 3.3 Update Seller Profile
```
PUT /sellers/{seller_id}
```
**Request Body** (name fields only — group leader changes handled via switch endpoint):
```json
{
  "first_name": "Anand",
  "last_name": "Rajesh"
}
```
**Response `200 OK`:** Updated seller object.  
**Errors:** `404 Not Found`, `422 Unprocessable Entity`

---

### 3.4 Check If Seller Can Switch Group Leader
```
GET /sellers/{seller_id}/can-switch
```
**Response `200 OK`:**
```json
{
  "can_switch": false,
  "reason": "Seller has outstanding inventory or unsettled collections. Please complete a return first."
}
```
or
```json
{
  "can_switch": true,
  "reason": null
}
```

---

### 3.5 Switch Group Leader (after return is completed)
```
POST /sellers/{seller_id}/switch-group-leader
```
**Request Body:**
```json
{
  "new_group_leader_id": "<uuid>",
  "new_bookstore_id": "<uuid>"
}
```
**Response `200 OK`:** Updated seller object with new `group_leader_id` and `bookstore_id`.  
**Errors:**
- `409 Conflict` — seller has outstanding inventory or unsettled money; return must be completed first.
- `404 Not Found`

---

## 4. Inventory Endpoints

### 4.1 Add Book to Inventory
```
POST /sellers/{seller_id}/inventory
```
**Request Body:**
```json
{
  "book_name": "Thirukkural",
  "language": "Tamil",
  "initial_count": 10,
  "cost_per_book": 50.00,
  "selling_price": 75.00
}
```
**Response `201 Created`:**
```json
{
  "book_id": "<uuid>",
  "seller_id": "<uuid>",
  "bookstore_id": "<uuid>",
  "book_name": "Thirukkural",
  "language": "Tamil",
  "initial_count": 10,
  "current_count": 10,
  "cost_per_book": 50.00,
  "selling_price": 75.00,
  "current_books_cost_balance": 500.00,
  "total_books_cost_balance": 500.00,
  "created_at": "2026-03-21T10:00:00Z"
}
```
**Errors:** `404 Not Found` (seller), `422 Unprocessable Entity`

---

### 4.2 List Seller Inventory
```
GET /sellers/{seller_id}/inventory
```
**Response `200 OK`:**
```json
{
  "seller_id": "<uuid>",
  "bookstore_id": "<uuid>",
  "books": [
    {
      "book_id": "<uuid>",
      "book_name": "Thirukkural",
      "language": "Tamil",
      "initial_count": 10,
      "current_count": 8,
      "cost_per_book": 50.00,
      "selling_price": 75.00,
      "current_books_cost_balance": 400.00,
      "total_books_cost_balance": 500.00
    }
  ],
  "summary": {
    "total_books_in_hand": 8,
    "total_cost_balance": 400.00,
    "total_initial_cost": 500.00
  }
}
```

---

### 4.3 Update Book in Inventory
```
PUT /sellers/{seller_id}/inventory/{book_id}
```
**Request Body** (any combination of fields — not current_count, that is managed by sales):
```json
{
  "book_name": "Thirukkural (Revised)",
  "selling_price": 80.00
}
```
**Response `200 OK`:** Updated inventory item.  
**Errors:** `404 Not Found`, `422 Unprocessable Entity`

---

### 4.4 Remove Book from Inventory
```
DELETE /sellers/{seller_id}/inventory/{book_id}
```
**Response `204 No Content`**  
**Errors:**
- `404 Not Found`
- `409 Conflict` — book has been partially sold (current_count < initial_count); cannot delete.

---

## 5. Sales Endpoints

### 5.1 Create New Sale
```
POST /sellers/{seller_id}/sales
```
**Request Body:**
```json
{
  "buyer_first_name": "Meena",
  "buyer_last_name": "Krishnan",
  "buyer_country_code": "+91",
  "buyer_phone": "9876543210",
  "items": [
    { "book_id": "<uuid>", "quantity_sold": 2 },
    { "book_id": "<uuid>", "quantity_sold": 1 }
  ]
}
```
**Response `201 Created`:**
```json
{
  "sale_id": "<uuid>",
  "seller_id": "<uuid>",
  "bookstore_id": "<uuid>",
  "buyer_first_name": "Meena",
  "buyer_last_name": "Krishnan",
  "buyer_country_code": "+91",
  "buyer_phone": "9876543210",
  "sale_items": [
    {
      "book_id": "<uuid>",
      "book_name": "Thirukkural",
      "language": "Tamil",
      "quantity_sold": 2,
      "selling_price": 75.00,
      "subtotal": 150.00
    }
  ],
  "total_books_sold": 3,
  "total_amount_collected": 225.00,
  "sale_date": "2026-03-21T11:30:00Z"
}
```
**Errors:**
- `400 Bad Request` — quantity_sold exceeds current_count for a book.
- `404 Not Found` — seller or book not found.
- `409 Conflict` — seller status is `pending_return`.
- `422 Unprocessable Entity` — validation failure.

**Side effects:** Decrements `current_count` for each book sold in the inventory table.

---

### 5.2 List Sales for a Seller
```
GET /sellers/{seller_id}/sales
```
**Query Parameters:**
- `limit` (optional, default 20): number of results to return.
- `from_date` (optional): filter sales from this date (ISO 8601).
- `to_date` (optional): filter sales up to this date (ISO 8601).

**Response `200 OK`:** Array of sale summary objects (without nested items).

---

### 5.3 Get Sale Detail
```
GET /sellers/{seller_id}/sales/{sale_id}
```
**Response `200 OK`:** Full sale object including `sale_items`.  
**Errors:** `404 Not Found`

---

## 6. Return Endpoints

### 6.1 Get Return Summary
```
GET /sellers/{seller_id}/return-summary
```
Returns the current state of what the seller needs to return to the bookstore.

**Response `200 OK`:**
```json
{
  "seller_id": "<uuid>",
  "bookstore": {
    "bookstore_id": "<uuid>",
    "store_name": "Sri Lakshmi Books",
    "owner_name": "Lakshmi Devi",
    "address": "12 MG Road, Chennai, TN 600001",
    "phone_number": "+914423456789"
  },
  "books_to_return": [
    {
      "book_id": "<uuid>",
      "book_name": "Thirukkural",
      "language": "Tamil",
      "quantity_to_return": 8,
      "cost_per_book": 50.00,
      "total_cost": 400.00
    }
  ],
  "total_books_to_return": 8,
  "total_cost_of_unsold_books": 400.00,
  "total_money_collected_from_sales": 225.00
}
```

---

### 6.2 Submit Return
```
POST /sellers/{seller_id}/returns
```
Records the physical return of books and money to the bookstore.

**Request Body:**
```json
{
  "notes": "Optional notes about the return"
}
```
**Response `201 Created`:**
```json
{
  "return_id": "<uuid>",
  "seller_id": "<uuid>",
  "bookstore_id": "<uuid>",
  "return_items": [...],
  "total_books_returned": 8,
  "total_money_returned": 225.00,
  "status": "completed",
  "return_date": "2026-03-21T18:00:00Z"
}
```
**Side effects:** Clears all inventory for the seller; resets `Seller.status` to `active`.

---

## 7. Group Leader Dashboard Endpoint

### 7.1 Get Group Leader Dashboard
```
GET /group-leaders/{group_leader_id}/dashboard
```
**Query Parameters:**
- `bookstore_id` (required): which bookstore context to show.
- `sort_by` (optional, default `total_amount_collected`): `total_books_sold` or `total_amount_collected`.
- `sort_order` (optional, default `desc`): `asc` or `desc`.

**Response `200 OK`:**
```json
{
  "group_leader": {
    "group_leader_id": "<uuid>",
    "name": "Ravi Kumar"
  },
  "bookstore": {
    "bookstore_id": "<uuid>",
    "store_name": "Sri Lakshmi Books"
  },
  "sellers": [
    {
      "seller_id": "<uuid>",
      "full_name": "Anand Raj",
      "total_books_sold": 25,
      "total_amount_collected": 1875.00
    },
    {
      "seller_id": "<uuid>",
      "full_name": "Priya Nair",
      "total_books_sold": 18,
      "total_amount_collected": 1350.00
    }
  ],
  "totals": {
    "total_books_sold": 43,
    "total_amount_collected": 3225.00
  }
}
```
**Errors:** `404 Not Found`, `400 Bad Request` (invalid sort parameters)

---

## HTTP Status Code Reference

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST (new resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Business rule violation (e.g., overselling) |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Duplicate or dependency conflict |
| 422 | Unprocessable Entity | Request body validation failure |
| 500 | Internal Server Error | Unexpected server error |
