"""BookRover Abstract Base Classes — layer contracts.

Every service and repository has a corresponding ABC defined here.
Concrete classes in services/ and repositories/ implement these ABCs.
Routers and services depend only on the ABCs — never on concretions.
This enforces strict one-way layer dependencies and enables isolated testing.

One file per domain:
  abstract_admin_service.py          — AbstractAdminService
  abstract_bookstore_repository.py   — AbstractBookstoreRepository
  abstract_group_leader_repository.py — AbstractGroupLeaderRepository
  abstract_seller_service.py         — AbstractSellerService
  abstract_seller_repository.py      — AbstractSellerRepository
  abstract_inventory_service.py      — AbstractInventoryService
  abstract_inventory_repository.py   — AbstractInventoryRepository
  abstract_sale_service.py           — AbstractSaleService
  abstract_sale_repository.py        — AbstractSaleRepository
  abstract_return_service.py         — AbstractReturnService
  abstract_return_repository.py      — AbstractReturnRepository
"""
