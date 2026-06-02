from dataclasses import dataclass
from datetime import datetime, timezone

from order_events import OrderPlaced

from order_api.application.ports import EventPublisher
from order_api.domain.order import Order

@dataclass(frozen=True)
class PlaceOrderCommand:
    order_id: str
    item_id: str
    quantity: int

class PlaceOrderHandler:
    def __init__(self, publisher: EventPublisher) -> None:
        self._publisher = publisher

    async def handle(self, cmd: PlaceOrderCommand) -> None:
        order = Order(
            order_id=cmd.order_id,
            item_id=cmd.item_id,
            quantity=cmd.quantity,
        )
        event = OrderPlaced(
            order_id=order.order_id,
            item_id=order.item_id,
            quantity=order.quantity,
            placed_at=datetime.now(timezone.utc),
        )
        await self._publisher.publish(event)