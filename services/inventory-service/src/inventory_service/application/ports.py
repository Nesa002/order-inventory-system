from abc import ABC, abstractmethod

from order_events import OrderResult

from inventory_service.domain.inventory import ReservationStatus

class InventoryRepository(ABC):
    @abstractmethod
    def reserve(self, item_id: str, quantity: int) -> ReservationStatus: ...

class ResultPublisher(ABC):
    @abstractmethod
    async def publish(self, result: OrderResult) -> None: ...