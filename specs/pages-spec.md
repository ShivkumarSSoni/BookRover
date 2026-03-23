# BookRover — Pages Specification

## Design Principles

- **Mobile-first**: all pages designed for 375px screen width. Scale up gracefully.
- **Touch-friendly**: minimum button size 44×44px.
- **No dropdowns on the New Buyer page** — as specified.
- **Simple language**: field labels must be plain English; no technical terms visible to users.
- **Tailwind CSS** for all styling — no inline styles.
- **One action per page section** — avoid cognitive overload.

---

## Page List

| Page | Route | Accessible By |
|------|-------|---------------|
| Login | `/login` | All |
| Seller Registration | `/register` | New sellers |
| Seller — Inventory | `/inventory` | Seller |
| Seller — New Buyer | `/new-buyer` | Seller |
| Seller — Return Books | `/return` | Seller |
| Group Leader Dashboard | `/dashboard` | Group Leader |
| Admin | `/admin` | Admin |

---

## 1. Login Page

**Route**: `/login`  
**Access**: All users

### Layout — Step 1: Email Entry
- App logo + name “BookRover” centered at top.
- Subtitle: “Book Selling Made Simple”
- Email address input field (full-width, mobile-friendly).
- “Continue” button (full-width, prominent).

### Layout — Step 2: OTP Verification (production only)
- Displayed after a successful email submission when `VITE_AUTH_MODE=cognito`.
- Heading: “Check your email”
- Sub-text: “We sent a sign-in code to {email}. It expires in 3 minutes.”
- 6-digit OTP code input field.
- “Verify” button.
- “Back” link to return to Step 1.

### Authentication Flow
- **Production** (`VITE_AUTH_MODE=cognito`): submitting the email triggers an AWS Cognito `USER_AUTH` challenge (email OTP); the user receives a one-time code by email; entering the code exchanges it for Cognito JWT tokens stored in `localStorage`.
- **Development** (`VITE_AUTH_MODE=mock`): submitting the email immediately issues a lightweight dev token; the OTP step is skipped entirely. The backend resolves the email to a BookRover profile and returns the user’s role.

---

## 2. Seller Registration Page

**Route**: `/register`  
**Access**: New sellers (any user without an existing seller profile)

### Purpose
Seller enters their details and links themselves to a group leader + bookstore.

### Fields

| Field | Type | Notes |
|-------|------|-------|
| First Name | Text input | Required. Max 50 chars. |
| Last Name | Text input | Required. Max 50 chars. |
| Email | Text input (email) | Required. Pre-filled from sign-in (Cognito email). |
| Group Leader + Bookstore | Dropdown | Required. Options fetched from `GET /group-leaders`. Display format: `"Ravi Kumar — Sri Lakshmi Books"`. Each option maps to `group_leader_id` + `bookstore_id`. |

### Actions
- **Register** button — calls `POST /sellers`. On success → redirect to `/inventory`.

### Validation
- All fields required before enabling Register button.
- Email must be a valid email format.

### Notes
- Group Leader dropdown is populated from `GET /group-leaders` on page load.
- If the list is empty, show: "No groups are set up yet. Contact your admin."

---

## 3. Inventory Page

**Route**: `/inventory`  
**Access**: Seller

### Purpose
Seller manages their personal book inventory — add, edit, remove books.

### Layout — Page Header
Below the top nav bar, display:
```
Welcome, {first_name}!
```
Small, friendly greeting using the seller's first name from localStorage / seller profile.

### Layout — Inventory Summary Bar (top, sticky)
| Label | Value |
|-------|-------|
| Books in Hand | Sum of `current_count` across all books |
| Total Cost Balance | Sum of `current_count × cost_per_book` across all books |

### Layout — Book List
Each book displayed as a **card**:
- Book Name (large, bold)
- Language (small label)
- In Hand: `{current_count}` / Initial: `{initial_count}`
- Cost: ₹`{cost_per_book}` | Sell: ₹`{selling_price}`
- Cost Balance: ₹`{current_count × cost_per_book}`
- **Edit** button (pencil icon) → opens the Edit Book form inline or as a modal.
- **Remove** button (trash icon) → confirms then calls `DELETE`. Disabled if book has been partially sold.

### Layout — Add Book Form (collapsible, at top of list)
"+ Add Book" button expands the form:

| Field | Type | Notes |
|-------|------|-------|
| Book Name | Text input | Required. Max 200 chars. |
| Language | Text input | Required. Max 50 chars. e.g., "Tamil", "English", "Hindi". |
| Count | Number input | Required. Min 1. |
| Cost per Book (₹) | Number input | Required. Min 0.01. 2 decimal places. |
| Selling Price (₹) | Number input | Required. Min 0.01. Must be > Cost per Book. |

- **Add Book** button → calls `POST /sellers/{seller_id}/inventory`. On success, form collapses and new book appears in list.
- **Cancel** button → collapses form without saving.

### Edit Book Form (inline/modal)
Same fields as Add Book, pre-filled with current values.  
`initial_count` and `current_count` are read-only (shown as info, not editable fields).  
- **Save** button → calls `PUT /sellers/{seller_id}/inventory/{book_id}`.
- **Cancel** button → closes form without saving.

### Empty State
If no books: "Your inventory is empty. Add your first book using the button above."

---

## 4. New Buyer Page

**Route**: `/new-buyer`  
**Access**: Seller

### Purpose
Seller records a sale at a buyer's door. Fast, tap-friendly, no typing for book selection.

### Layout — Page Header
Below the top nav bar, display:
```
Selling as: {first_name} {last_name}
```
Reminds the seller whose account is active during a sale.

### Layout — Section 1: Book Selection

**Header**: "Select Books to Sell"

Each available book (where `current_count > 0`) displayed as a **row**:

```
[ Book Name ]         [ Language ]
[ - ]  [ 0 ]  [ + ]
```

- **Book Name**: large text, not editable.
- **Language**: small label below book name.
- **`-` button**: decrements the quantity for this book. Disabled when quantity is 0.
- **Quantity field**: read-only numeric display. Shows `0` by default.
- **`+` button**: increments the quantity. Disabled when quantity = `current_count` (cannot sell more than available).
- Books with `current_count = 0` are **not shown** on this page.

No dropdowns. No text inputs in this section.

**Running Total Bar** (sticky, visible at bottom of screen):
```
Books: {total_books_selected}    Total: ₹{total_amount}
```
- Updates in real-time as `+`/`-` buttons are tapped.
- `₹` symbol (or configured currency symbol).

---

### Layout — Section 2: Buyer Details

**Header**: "Buyer Information"

| Field | Type | Notes |
|-------|------|-------|
| First Name | Text input | Required. Max 50 chars. |
| Last Name | Text input | Required. Max 50 chars. |
| Country Code | Text input | Required. Defaulted to `+91`. Editable. Max 5 chars. |
| Phone Number | Number input | Required. 5–15 digits. No spaces or dashes. |

---

### Layout — Section 3: Actions

- **Save Sale** button — full width, large, prominent.
  - Disabled if: no books selected OR buyer name is empty OR phone is empty.
  - On tap → calls `POST /sellers/{seller_id}/sales`.
  - On success → shows confirmation: "Sale saved! ✓ {total_books_selected} books — ₹{total_amount}" and resets the page for Next Buyer.
  - On error → shows error message below the button.
- **Clear** button — resets all quantities to 0 and clears buyer details.

### After Save
- All quantities reset to 0.
- Buyer details cleared.
- Running total resets to 0.
- Seller can immediately start the next buyer's transaction.

### Validation
- At least one book must have quantity > 0.
- First Name, Last Name: required, non-empty.
- Phone Number: digits only, 5–15 characters.
- Country Code: starts with `+`, max 5 chars.

---

## 5. Return Books Page

**Route**: `/return`  
**Access**: Seller

### Purpose
Shows the seller what they need to physically bring back to the bookstore — unsold books + collected money.

### Layout — Bookstore Info Card (top)
```
Returning to: {bookstore.store_name}
Owner: {bookstore.owner_name}
Address: {bookstore.address}
Phone: {bookstore.phone_number}
```

### Layout — Books to Return Table

| Book Name | Language | Qty | Cost | Total |
|-----------|----------|-----|------|-------|
| Thirukkural | Tamil | 8 | ₹50 | ₹400 |
| Bible Stories | English | 3 | ₹80 | ₹240 |

- Read-only. No editing allowed on this page.
- Shows only books with `current_count > 0`.

### Layout — Summary Cards

```
┌─────────────────────┐   ┌─────────────────────┐
│  Unsold Books       │   │  Money to Return     │
│  11 books           │   │  ₹640               │
│  Cost: ₹640         │   │  (from your sales)   │
└─────────────────────┘   └─────────────────────┘
```

- Left card: total books to return + their total cost.
- Right card: total money collected from all sales (to be handed over to bookstore).

### Layout — Action

- **Submit Return** button — full width. Calls `POST /sellers/{seller_id}/returns`.
  - Before submitting, shows confirmation dialog: "Are you sure? This will clear your inventory."
  - On success → shows: "Return submitted successfully." Inventory cleared. If seller had requested a group leader switch, allows them to re-register.
  - On error → shows error message.

### Empty State
If all books are sold (`current_count = 0` for all): "All books sold! Nothing to return. Your money to return: ₹{total_money_collected}."

---

## 6. Group Leader Dashboard

**Route**: `/dashboard`  
**Access**: Group Leader

### Purpose
Shows the group leader a summary of all their sellers' performance for a selected bookstore.

### Layout — Header
```
Group Leader: {name}
Bookstore: {store_name}   [Change]
```
- If group leader has multiple bookstores, "Change" opens a bookstore selector.

### Layout — Sellers Table

| Seller Name | Books Sold | Money Collected |
|-------------|-----------|-----------------|
| Anand Raj | 25 | ₹1,875 |
| Priya Nair | 18 | ₹1,350 |
| **Total** | **43** | **₹3,225** |

- Default sort: **Money Collected, descending**.
- Column headers for "Books Sold" and "Money Collected" are **tappable** to toggle sort:
  - First tap: ascending.
  - Second tap: descending.
  - Active sort column shows an arrow indicator (↑ or ↓).
- Totals row is always at the bottom, never sorted.
- Calls: `GET /group-leaders/{id}/dashboard?bookstore_id=<id>&sort_by=<field>&sort_order=<order>`

### Layout — Summary Cards (above table)
```
┌─────────────────┐   ┌─────────────────┐
│ Total Sellers   │   │ Total Collected  │
│ 2               │   │ ₹3,225          │
└─────────────────┘   └─────────────────┘
```

### Empty State
If no sellers registered: "No sellers registered under you yet."

---

## 7. Admin Page

**Route**: `/admin`  
**Access**: Admin only — not visible to sellers or group leaders.

### Purpose
CRUD management for Group Leaders and BookStores.

### Layout — Tabs
```
[ Group Leaders ]  [ Bookstores ]
```

---

### Tab 1: Group Leaders

**List**: Each group leader shown as a card:
- Name, Email
- Linked bookstores: comma-separated store names
- **Edit** button → opens edit form.
- **Delete** button → confirms then deletes. Disabled if active sellers are assigned.

**Add Group Leader Form** (collapsible, "+ Add Group Leader" button):

| Field | Type | Notes |
|-------|------|-------|
| Name | Text input | Required. Max 100 chars. |
| Email | Text input (email) | Required. |
| Bookstores | Multi-select checkboxes | Required. At least 1. List of all bookstores. |

- **Save** → calls `POST /admin/group-leaders`.

**Edit Group Leader Form** (same fields, pre-filled):
- **Save** → calls `PUT /admin/group-leaders/{id}`.

---

### Tab 2: Bookstores

**List**: Each bookstore shown as a card:
- Store Name, Owner Name, Address, Phone Number
- **Edit** button → opens edit form.
- **Delete** button → confirms then deletes. Disabled if inventory or returns are associated.

**Add Bookstore Form** (collapsible, "+ Add Bookstore" button):

| Field | Type | Notes |
|-------|------|-------|
| Store Name | Text input | Required. Max 100 chars. |
| Owner Name | Text input | Required. Max 100 chars. |
| Address | Textarea | Required. Max 500 chars. |
| Phone Number | Text input | Required. Max 20 chars. |

- **Save** → calls `POST /admin/bookstores`.

**Edit Bookstore Form** (same fields, pre-filled):
- **Save** → calls `PUT /admin/bookstores/{id}`.

---

## Navigation Bar (top nav)

Shown on all pages except Login and Registration. Fixed at the top of the screen, full-width. On seller pages, displays the seller's full name on the left followed by the nav links on the right.

### Seller Nav
```
[ BookRover ]  Anand Raj          [ Inventory ]  [ New Buyer ]  [ Return ]
```
- Seller's full name (`first_name + last_name`) is displayed prominently in the top bar.
- Name is fetched from `GET /sellers/{seller_id}` on first load and cached in state.
- Each nav link highlights (active style) when its route is current.

### Group Leader Nav
```
[ BookRover ]                               [ Dashboard ]
```

### Admin Nav
```
[ BookRover ]                                  [ Admin ]
```

---

## Global UI Conventions

- **Loading state**: show a spinner centered on the page while API calls are in progress. Disable action buttons during loading.
- **Error messages**: shown in a red banner below the relevant section. Auto-dismiss after 5 seconds, or dismissible by tap.
- **Success messages**: shown in a green banner. Auto-dismiss after 3 seconds.
- **Confirmation dialogs**: for destructive actions (Delete, Submit Return). Plain modal with "Confirm" and "Cancel" buttons.
- **Currency**: display as `₹{amount}` with 2 decimal places. Symbol configurable via environment variable for future multi-currency support.
- **Empty states**: always show a helpful message — never a blank screen.
- **Form validation**: validate on blur (when user leaves a field) and on submit. Show inline error messages directly below the invalid field.
