"""BookRover API routers — HTTP layer.

Each router module handles one domain:
  admin.py       — group leader and bookstore CRUD (Admin only)
  sellers.py     — seller registration and profile management
  inventory.py   — per-seller book inventory
  sales.py       — sale recording and history
  returns.py     — return summary and submission
  dashboard.py   — group leader performance dashboard
  lookups.py     — public lookup endpoints for registration dropdowns
"""
