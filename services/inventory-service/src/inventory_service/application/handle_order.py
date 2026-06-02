from datetime import datetime, timezone

import structlog

from order_events import OrderPlaced, OrderResult

from inventory_service.application.ports import InventoryRepository, ResultPublisher
from inventory_service.domain.inventory import ReservationStatus

log = structlog.get_logger()

class HandleOrderHandler:
    def __init__(self, repo: InventoryRepository, publisher: ResultPublisher) -> None:
        self._repo = repo
        self._publisher = publisher
        self._processed_ids: set[str] = set()

    async def handle(self, event: OrderPlaced) -> None:
        if event.order_id in self._processed_ids:
            log.info("order_skipped_duplicate", order_id=event.order_id)
            return

        status = self._repo.reserve(event.item_id, event.quantity)
        reason = (
            None
            if status == ReservationStatus.RESERVED
            else f"insufficient stock for {event.item_id}"
        )

        result = OrderResult(
            order_id=event.order_id,
            status=status.value,
            reason=reason,
            processed_at=datetime.now(timezone.utc),
        )

        await self._publisher.publish(result)
        self._processed_ids.add(event.order_id)

        log.info(
            "order_processed",
            order_id=event.order_id,
            item_id=event.item_id,
            quantity=event.quantity,
            status=status.value,
            reason=reason,
        )