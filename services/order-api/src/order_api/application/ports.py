from abc import ABC, abstractmethod

from order_events import OrderPlaced

class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: OrderPlaced) -> None: ...