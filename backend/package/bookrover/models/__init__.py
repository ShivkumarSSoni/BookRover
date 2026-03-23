"""BookRover Pydantic models — Data Transfer Objects (DTOs).

Pydantic models serve as the contract between HTTP ↔ service ↔ repository layers.
Raw dicts are never passed between layers — always use typed models.

One file per domain:
  admin.py        — BookStore and GroupLeader request/response models
  seller.py       — Seller request/response models
  inventory.py    — InventoryItem request/response models
  sale.py         — Sale and SaleItem request/response models
  return_model.py — Return and ReturnItem request/response models
"""
