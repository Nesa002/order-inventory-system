from inventory_service.application.ports import InventoryRepository
from inventory_service.domain.inventory import InventoryAggregate, ReservationStatus

class InMemoryInventoryRepository(InventoryRepository):
    def __init__(self, initial_stock: dict[str, int]) -> None:
        self._aggregate = InventoryAggregate()
        self._aggregate.seed(initial_stock)

    def reserve(self, item_id: str, quantity: int) -> ReservationStatus:
        return self._aggregate.reserve(item_id, quantity)