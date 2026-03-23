# BookRover — Data Models

All entities are stored in **AWS DynamoDB**. Each entity has its own table (multi-table design for clarity). Table names follow the pattern `bookrover-<entity>-<env>` where `<env>` is `dev` or `prod`.

All primary keys (`id`) are **UUID v4 strings**.  
All timestamps are **ISO 8601 UTC strings** (`2026-03-21T10:30:00Z`).

---

## Entity Relationship Summary

```
Admin (separate login)
  |
  +-- manages --> GroupLeader
                     |
                     +-- linked to --> BookStore (1 or many)
                     |
                     +-- oversees --> Seller
                                        |
                                        +-- has --> InventoryItem (per book, per seller)
                                        |
                                        +-- creates --> Sale
                                        |                  |
                                        |                  +-- contains --> SaleItem
                                        |
                                        +-- submits --> Return
                                                           |
                                                           +-- contains --> ReturnItem
```

---

## 1. Admin

**DynamoDB Table**: `bookrover-admins-<env>`

| Field | Type | Description |
|-------|------|-------------|
| `admin_id` | String (UUID) | Partition Key |
| `email` | String | Email address (unique) |
| `created_at` | String (ISO 8601) | Creation timestamp |

**Access patterns:**
- Get admin by email (for login validation)

---

## 2. BookStore

**DynamoDB Table**: `bookrover-bookstores-<env>`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `bookstore_id` | String (UUID) | PK | Unique identifier |
| `store_name` | String | 1–100 chars | Name of the bookstore |
| `owner_name` | String | 1–100 chars | Name of the bookstore owner |
| `address` | String | 1–500 chars | Full street address |
| `phone_number` | String | 1–20 chars | Contact phone number |
| `created_at` | String (ISO 8601) | | Creation timestamp |
| `updated_at` | String (ISO 8601) | | Last updated timestamp |

**Access patterns:**
- List all bookstores (for Admin page and dropdowns)
- Get bookstore by `bookstore_id`

---

## 3. GroupLeader

**DynamoDB Table**: `bookrover-group-leaders-<env>`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `group_leader_id` | String (UUID) | PK | Unique identifier |
| `name` | String | 1–100 chars | Full name |
| `email` | String | valid email | Email address (for Cognito auth) |
| `bookstore_ids` | List[String] | min 1 | List of associated bookstore UUIDs |
| `created_at` | String (ISO 8601) | | Creation timestamp |
| `updated_at` | String (ISO 8601) | | Last updated timestamp |

**Notes:**
- A group leader can be linked to **multiple bookstores**.
- The seller's registration dropdown shows `group_leader.name + bookstore.store_name` combinations.

**Access patterns:**
- List all group leaders (for Seller registration dropdown)
- Get group leader by `group_leader_id`
- Get sellers under a group leader (via Seller table GSI)

---

## 4. Seller

**DynamoDB Table**: `bookrover-sellers-<env>`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `seller_id` | String (UUID) | PK | Unique identifier |
| `first_name` | String | 1–50 chars | First name |
| `last_name` | String | 1–50 chars | Last name |
| `email` | String | valid email | Email address (for Cognito auth) |
| `group_leader_id` | String (UUID) | required | Currently assigned group leader |
| `bookstore_id` | String (UUID) | required | Currently assigned bookstore |
| `status` | String (Enum) | | `active` or `pending_return` |
| `created_at` | String (ISO 8601) | | Registration timestamp |
| `updated_at` | String (ISO 8601) | | Last updated timestamp |

**Status Values:**
- `active` — seller can record sales; cannot switch group leader.
- `pending_return` — seller has requested to switch group leader; must complete return first.

**GSI (Global Secondary Index):**
- `group-leader-id-index` on `group_leader_id` — enables fetching all sellers under a group leader for the dashboard.

**Access patterns:**
- Get seller by `seller_id`
- Get seller by `email` (for Cognito auth lookup)
- List sellers by `group_leader_id` (GSI) — for Group Leader Dashboard

---

## 5. InventoryItem (Book)

**DynamoDB Table**: `bookrover-inventory-<env>`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `book_id` | String (UUID) | PK | Unique identifier |
| `seller_id` | String (UUID) | required | Owning seller |
| `bookstore_id` | String (UUID) | required | Bookstore where book was collected from |
| `book_name` | String | 1–200 chars | Title of the book |
| `language` | String | 1–50 chars | Language of the book (e.g., "English", "Tamil") |
| `initial_count` | Integer | ≥ 1 | Total books collected from the bookstore |
| `current_count` | Integer | ≥ 0 | Books currently in hand (not yet sold or returned) |
| `cost_per_book` | Decimal | ≥ 0.01 | Cost price per book (from bookstore) |
| `selling_price` | Decimal | ≥ 0.01 | Selling price per book (to buyer) |
| `created_at` | String (ISO 8601) | | When book was added to inventory |
| `updated_at` | String (ISO 8601) | | Last updated (after each sale) |

**Computed Fields** (not stored; calculated on read):
- `current_books_cost_balance` = `current_count × cost_per_book`
- `total_books_cost_balance` = `initial_count × cost_per_book`
- `current_total_books_count_balance` = sum of `current_count` across all books for a seller

**GSI:**
- `seller-id-index` on `seller_id` — list all books for a seller.
- `bookstore-id-index` on `bookstore_id` — list all books sourced from a bookstore.

**Access patterns:**
- List all inventory for a seller (GSI: `seller_id-index`)
- Get specific book by `book_id`
- Update `current_count` after a sale

---

## 6. Sale

**DynamoDB Table**: `bookrover-sales-<env>`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `sale_id` | String (UUID) | PK | Unique identifier |
| `seller_id` | String (UUID) | required | Seller who made the sale |
| `bookstore_id` | String (UUID) | required | Bookstore the books were sourced from |
| `buyer_first_name` | String | 1–50 chars | Buyer's first name |
| `buyer_last_name` | String | 1–50 chars | Buyer's last name |
| `buyer_country_code` | String | e.g., "+91" | Phone country code (default: "+91") |
| `buyer_phone` | String | 5–15 digits | Buyer's phone number (digits only) |
| `sale_items` | List[SaleItem] | min 1 item | Books sold in this transaction |
| `total_books_sold` | Integer | ≥ 1 | Total number of books sold (sum of all item quantities) |
| `total_amount_collected` | Decimal | ≥ 0.01 | Total money collected (sum of all item subtotals) |
| `sale_date` | String (ISO 8601) | | Date and time of sale |
| `created_at` | String (ISO 8601) | | Record creation timestamp |

**GSI:**
- `seller-id-index` on `seller_id` — list all sales by a seller.
- `bookstore-id-index` on `bookstore_id` — list all sales from a bookstore's inventory.

---

## 7. SaleItem (embedded in Sale)

Stored as a **nested list** inside the `Sale` document (not a separate table).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `book_id` | String (UUID) | required | Reference to the InventoryItem |
| `book_name` | String | | Snapshot of book name at time of sale |
| `language` | String | | Snapshot of language at time of sale |
| `quantity_sold` | Integer | ≥ 1 | Number of copies sold |
| `selling_price` | Decimal | ≥ 0.01 | Price per copy at time of sale |
| `subtotal` | Decimal | ≥ 0.01 | `quantity_sold × selling_price` |

**Note**: `book_name`, `language`, and `selling_price` are **snapshotted** at sale time. If a book's details change later, historical sales remain accurate.

---

## 8. Return

**DynamoDB Table**: `bookrover-returns-<env>`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `return_id` | String (UUID) | PK | Unique identifier |
| `seller_id` | String (UUID) | required | Seller submitting the return |
| `bookstore_id` | String (UUID) | required | Bookstore receiving the return |
| `return_items` | List[ReturnItem] | | Books being returned |
| `total_books_returned` | Integer | ≥ 0 | Total number of books returned |
| `total_money_returned` | Decimal | ≥ 0 | Total money collected from sales, to be returned |
| `status` | String (Enum) | | `pending` or `completed` |
| `return_date` | String (ISO 8601) | | Date of return submission |
| `created_at` | String (ISO 8601) | | Record creation timestamp |

**Status Values:**
- `pending` — return initiated but not yet confirmed.
- `completed` — return confirmed; seller status reset to allow group leader switch if requested.

**GSI:**
- `seller-id-index` on `seller_id` — get all returns by a seller.

---

## 9. ReturnItem (embedded in Return)

Stored as a **nested list** inside the `Return` document.

| Field | Type | Description |
|-------|------|-------------|
| `book_id` | String (UUID) | Reference to InventoryItem |
| `book_name` | String | Snapshot of book name |
| `language` | String | Snapshot of language |
| `quantity_returned` | Integer | Number of copies returned (= current_count at time of return) |
| `cost_per_book` | Decimal | Cost price per copy |
| `total_cost` | Decimal | `quantity_returned × cost_per_book` |

---

## DynamoDB Table Summary

| Table Name (dev) | PK | GSIs |
|------------------|----|------|
| `bookrover-admins-dev` | `admin_id` | — |
| `bookrover-bookstores-dev` | `bookstore_id` | — |
| `bookrover-group-leaders-dev` | `group_leader_id` | — |
| `bookrover-sellers-dev` | `seller_id` | `group-leader-id-index` |
| `bookrover-inventory-dev` | `book_id` | `seller-id-index`, `bookstore-id-index` |
| `bookrover-sales-dev` | `sale_id` | `seller-id-index`, `bookstore-id-index` |
| `bookrover-returns-dev` | `return_id` | `seller-id-index` |

---

## Data Integrity Rules

1. When a **Sale** is saved, `InventoryItem.current_count` is decremented atomically for each book sold.
2. A sale item's quantity cannot exceed `InventoryItem.current_count` at the time of sale.
3. A seller with `status = pending_return` cannot create new sales.
4. When a **Return** is completed, the seller's inventory is cleared and `Seller.status` may be reset.
5. A `GroupLeader` cannot be deleted if sellers are actively assigned to them.
6. A `BookStore` cannot be deleted if it has associated inventory or pending returns.
