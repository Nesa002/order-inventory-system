import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI

from order_api.api.routes.orders import router
from order_api.application.place_order import PlaceOrderHandler
from order_api.config import settings
from order_api.infrastructure.kafka.producer import KafkaEventPublisher

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        enable_idempotence=True,
        acks="all",
    )
    await producer.start()
    log.info("kafka_producer_started", bootstrap_servers=settings.kafka_bootstrap_servers)

    app.state.place_order_handler = PlaceOrderHandler(KafkaEventPublisher(producer))

    try:
        yield
    finally:
        await producer.stop()
        log.info("kafka_producer_stopped")

def create_app() -> FastAPI:
    app = FastAPI(title="Order API", lifespan=lifespan)
    app.include_router(router)
    return app

app = create_app()