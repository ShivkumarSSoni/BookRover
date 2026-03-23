"""BookRover repository layer — DynamoDB data access.

Repositories are the ONLY layer permitted to call DynamoDB via boto3.
They implement repository ABCs from interfaces/ and raise domain exceptions
from exceptions/ — never boto3 ClientError.

One file per entity:
  bookstore_repository.py       — BookStore CRUD
  group_leader_repository.py    — GroupLeader CRUD
  seller_repository.py          — Seller CRUD + GSI queries
  inventory_repository.py       — InventoryItem CRUD + GSI queries
  sale_repository.py            — Sale writes + GSI queries
  return_repository.py          — Return writes + GSI queries
"""
