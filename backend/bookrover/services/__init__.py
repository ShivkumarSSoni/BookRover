"""BookRover service layer — business logic.

Services own all business rules and orchestration. They depend on repository
ABCs from interfaces/ (injected via constructor) and never call DynamoDB directly.
Routers depend on service ABCs — never on concrete service classes.

One file per domain:
  admin_service.py     — BookStore and GroupLeader management
  seller_service.py    — Seller registration, profile, group leader switch
  inventory_service.py — Book inventory management
  sale_service.py      — Sale recording and retrieval
  return_service.py    — Return summary calculation and submission
"""
