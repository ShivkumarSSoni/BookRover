# arc42 — Section 6: Runtime View

Key scenarios showing how BookRover components interact at runtime.

---

## Scenario 1: Seller Records a Sale at a Buyer's Door

```
Seller (Phone Browser)
        │
        │  1. Opens /new-buyer page
        │  2. Page loads inventory: GET /sellers/{seller_id}/inventory
        │
        ▼
   React Frontend
        │
        │  3. Renders book list with +/- buttons
        │  4. Seller taps + on 2 books, fills buyer details
        │  5. Taps "Save Sale"
        │
        │  POST /sellers/{seller_id}/sales
        │  Body: { buyer details, items: [{book_id, quantity_sold}] }
        │
        ▼
  API Gateway (HTTP API)
        │
        │  6. Validates request; forwards to Lambda
        │
        ▼
  Lambda (FastAPI via Mangum)
        │
        │  Router → SaleService → SaleRepository
        │
        │  7. SaleService checks seller status = "active"
        │  8. For each item: checks quantity_sold ≤ current_count
        │  9. SaleRepository:
        │     a. Writes Sale record to bookrover-sales table
        │     b. UpdateExpression decrements current_count for each book
        │        in bookrover-inventory table (atomic)
        │
        │  10. Returns 201 Created with sale summary
        │
        ▼
   React Frontend
        │
        │  11. Shows success banner: "Sale saved! 3 books — ₹225"
        │  12. Resets page for next buyer (quantities → 0, fields cleared)
```

---

## Scenario 2: Admin Creates a New Group Leader

```
Admin (Phone Browser)
        │
        │  1. Opens /admin → Group Leaders tab
        │  2. Taps "+ Add Group Leader"
        │  3. Fills name, email, selects bookstores
        │  4. Taps "Save"
        │
        │  POST /admin/group-leaders
        │
        ▼
  Lambda (FastAPI)
        │
        │  Router → AdminService → GroupLeaderRepository
        │
        │  5. AdminService checks email uniqueness
        │  6. AdminService validates each bookstore_id exists
        │  7. GroupLeaderRepository writes to bookrover-group-leaders table
        │
        │  Returns 201 Created
        │
        ▼
   React Frontend
        │
        │  8. New group leader appears in list
```

---

## Scenario 3: Seller Submits a Return

```
Seller (Phone Browser)
        │
        │  1. Opens /return page
        │  2. GET /sellers/{seller_id}/return-summary
        │
        ▼
  Lambda (FastAPI)
        │
        │  ReturnService:
        │  a. Queries bookrover-inventory (seller_id-index) → unsold books
        │  b. Queries bookrover-sales (seller_id-index) → total money collected
        │  c. Builds return summary response
        │
        ▼
   React Frontend
        │
        │  3. Displays return summary table + bookstore info
        │  4. Seller taps "Submit Return"
        │  5. Confirmation dialog shown
        │  6. Seller confirms
        │
        │  POST /sellers/{seller_id}/returns
        │
        ▼
  Lambda (FastAPI)
        │
        │  ReturnService:
        │  a. Creates Return record (snapshot of all unsold books)
        │  b. Clears current_count = 0 for all seller's books
        │  c. Updates seller.status = "active"
        │
        │  Returns 201 Created
        │
        ▼
   React Frontend
        │
        │  7. Shows "Return submitted successfully."
        │  8. If seller had requested a group leader switch → allows re-registration
```

---

## Scenario 4: Group Leader Views Dashboard

```
Group Leader (Phone Browser)
        │
        │  1. Opens /dashboard
        │  2. Selects bookstore (if multiple linked)
        │
        │  GET /group-leaders/{id}/dashboard?bookstore_id=<id>&sort_by=total_amount_collected&sort_order=desc
        │
        ▼
  Lambda (FastAPI)
        │
        │  DashboardService:
        │  a. Queries bookrover-sellers (group_leader_id-index) → all sellers
        │  b. For each seller: queries bookrover-sales (seller_id-index) → aggregates
        │     total_books_sold and total_amount_collected
        │  c. Sorts sellers by requested field + order
        │  d. Computes group totals
        │
        │  Returns dashboard response
        │
        ▼
   React Frontend
        │
        │  3. Renders seller table sorted by money collected (desc)
        │  4. Group leader taps column header to re-sort
        │  5. GET is called again with updated sort parameters
```

---

## Scenario 5: Seller Requests Group Leader Switch (Blocked)

```
Seller (Phone Browser)
        │
        │  1. Seller wants to switch group leader
        │  2. App calls GET /sellers/{seller_id}/can-switch
        │
        ▼
  Lambda (FastAPI)
        │
        │  SellerService:
        │  a. Checks if any inventory book has current_count > 0
        │  b. Checks if total_money_collected from sales > 0 (unsettled)
        │  c. → Returns can_switch: false
        │
        ▼
   React Frontend
        │
        │  3. Shows message: "You must return all books and money
        │     to the bookstore before switching."
        │  4. "Go to Return Page" button shown
```
