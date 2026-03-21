# arc42 — Section 5: Building Block View

## 5.1 Level 1 — System Overview

```
┌───────────────────────────────────────────────────────┐
│                     BookRover System                   │
│                                                       │
│   ┌─────────────┐          ┌─────────────────────┐    │
│   │   Frontend  │  HTTPS   │      Backend        │    │
│   │  (React SPA)│ ◄──────► │  (FastAPI / Lambda) │    │
│   └─────────────┘          └──────────┬──────────┘    │
│                                       │               │
│                              ┌────────▼────────┐      │
│                              │    DynamoDB     │      │
│                              │   (7 tables)    │      │
│                              └─────────────────┘      │
└───────────────────────────────────────────────────────┘
```

---

## 5.2 Level 2 — Frontend Breakdown

```
frontend/src/
├── pages/               # One component per page/route
│   ├── LoginPage
│   ├── SellerRegistrationPage
│   ├── InventoryPage
│   ├── NewBuyerPage
│   ├── ReturnBooksPage
│   ├── GroupLeaderDashboardPage
│   └── AdminPage
│
├── components/          # Reusable UI building blocks
│   ├── BookCard         # Displays a single book in inventory
│   ├── BookSaleRow      # +/- row on New Buyer page
│   ├── BuyerForm        # Buyer details fields
│   ├── RunningTotal     # Sticky total bar on New Buyer page
│   ├── SummaryCard      # Generic metric card (books/money)
│   ├── SellerTable      # Group leader dashboard table
│   ├── ConfirmDialog    # Confirmation modal
│   └── NavBar           # Bottom navigation bar
│
├── hooks/               # Data fetching and state logic
│   ├── useInventory     # Fetch + mutate seller inventory
│   ├── useSales         # Create + list sales
│   ├── useReturn        # Fetch return summary + submit return
│   ├── useDashboard     # Fetch group leader dashboard data
│   └── useAdmin         # Group leaders + bookstores CRUD
│
├── services/            # Raw API call functions (axios)
│   ├── inventoryService
│   ├── salesService
│   ├── returnService
│   ├── sellerService
│   ├── groupLeaderService
│   └── adminService
│
├── context/             # Global state providers
│   ├── AuthContext      # Current user identity and role
│   └── SellerContext    # Current seller profile + bookstore
│
└── utils/
    ├── formatCurrency   # Format number as ₹1,234.50
    └── formatDate       # Format ISO timestamp as readable date
```

---

## 5.3 Level 2 — Backend Breakdown

```
backend/app/
├── main.py              # App factory — creates FastAPI instance,
│                        # registers routers, configures middleware (CORS, logging)
│
├── config.py            # Typed config via pydantic-settings BaseSettings
│                        # Reads APP_ENV, DYNAMODB_ENDPOINT_URL, DYNAMODB_REGION, etc.
│
├── dependencies.py      # Shared FastAPI Depends() functions
│                        # get_dynamodb_resource(), get_settings()
│
├── routers/             # HTTP layer — one file per domain
│   ├── admin.py         # POST/GET/PUT/DELETE /admin/group-leaders, /admin/bookstores
│   ├── sellers.py       # POST/GET/PUT /sellers, /sellers/{id}/can-switch, /switch-group-leader
│   ├── inventory.py     # POST/GET/PUT/DELETE /sellers/{id}/inventory
│   ├── sales.py         # POST/GET /sellers/{id}/sales
│   ├── returns.py       # GET /sellers/{id}/return-summary, POST /sellers/{id}/returns
│   ├── dashboard.py     # GET /group-leaders/{id}/dashboard
│   └── lookups.py       # GET /bookstores, GET /group-leaders (for dropdowns)
│
├── models/              # Pydantic schemas (request bodies + response models)
│   ├── admin.py
│   ├── seller.py
│   ├── inventory.py
│   ├── sale.py
│   └── return_model.py
│
├── services/            # Business logic — no DynamoDB calls here
│   ├── admin_service.py
│   ├── seller_service.py
│   ├── inventory_service.py
│   ├── sale_service.py
│   └── return_service.py
│
├── repositories/        # DynamoDB access — only layer that calls boto3
│   ├── bookstore_repository.py
│   ├── group_leader_repository.py
│   ├── seller_repository.py
│   ├── inventory_repository.py
│   ├── sale_repository.py
│   └── return_repository.py
│
└── utils/
    ├── id_generator.py      # uuid4() as string
    ├── timestamp.py         # utcnow().isoformat() + "Z"
    └── logger.py            # Structured JSON logger factory
```

---

## 5.4 DynamoDB Tables (Data Layer)

| Table | Primary Key | GSIs |
|-------|------------|------|
| `bookrover-admins-<env>` | `admin_id` | — |
| `bookrover-bookstores-<env>` | `bookstore_id` | — |
| `bookrover-group-leaders-<env>` | `group_leader_id` | — |
| `bookrover-sellers-<env>` | `seller_id` | `group_leader_id-index` |
| `bookrover-inventory-<env>` | `book_id` | `seller_id-index`, `bookstore_id-index` |
| `bookrover-sales-<env>` | `sale_id` | `seller_id-index`, `bookstore_id-index` |
| `bookrover-returns-<env>` | `return_id` | `seller_id-index` |

Full schema in `specs/data-models.md`.
