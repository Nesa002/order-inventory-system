from dataclasses import dataclass

@dataclass(frozen=True)
class Order:
    order_id: str
    item_id: str
    quantity: int