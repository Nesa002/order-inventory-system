from datetime import datetime
from typing import Literal

from pydantic import BaseModel

class OrderPlaced(BaseModel):
    event_type: Literal["OrderPlaced"] = "OrderPlaced"
    order_id: str
    item_id: str
    quantity: int
    placed_at: datetime

class OrderResult(BaseModel):
    event_type: Literal["OrderResult"] = "OrderResult"
    order_id: str
    status: Literal["reserved", "rejected"]
    reason: str | None = None
    processed_at: datetime
