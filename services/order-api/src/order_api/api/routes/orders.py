import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from order_api.application.place_order import PlaceOrderCommand, PlaceOrderHandler

log = structlog.get_logger()
router = APIRouter()

class OrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_id: str = Field(alias="orderId")
    item_id: str = Field(alias="itemId")
    quantity: int

def _get_handler(request: Request) -> PlaceOrderHandler:
    return request.app.state.place_order_handler

@router.post("/orders", status_code=status.HTTP_202_ACCEPTED)
async def place_order(
    body: OrderRequest,
    handler: PlaceOrderHandler = Depends(_get_handler),
) -> dict:
    log.info("order_received", order_id=body.order_id, item_id=body.item_id, quantity=body.quantity)
    try:
        await handler.handle(
            PlaceOrderCommand(
                order_id=body.order_id,
                item_id=body.item_id,
                quantity=body.quantity,
            )
        )
    except Exception as exc:
        log.error("order_publish_failed", order_id=body.order_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to publish order event")

    log.info("order_accepted", order_id=body.order_id)
    return {"orderId": body.order_id, "status": "accepted"}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}