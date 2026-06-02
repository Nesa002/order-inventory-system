from dataclasses import dataclass, field
from enum import Enum

class ReservationStatus(Enum):
    RESERVED = "reserved"
    REJECTED = "rejected"

@dataclass
class InventoryAggregate:
    _stock: dict[str, int] = field(default_factory=dict)

    def seed(self, stock: dict[str, int]) -> None:
        self._stock = dict(stock)

    def reserve(self, item_id: str, quantity: int) -> ReservationStatus:
        if self._stock.get(item_id, 0) >= quantity:
            self._stock[item_id] -= quantity
            return ReservationStatus.RESERVED
        return ReservationStatus.REJECTED

    def stock_level(self, item_id: str) -> int:
        return self._stock.get(item_id, 0)