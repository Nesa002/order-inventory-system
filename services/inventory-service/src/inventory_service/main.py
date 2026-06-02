import asyncio
import logging
import signal

import structlog
from aiokafka import AIOKafkaProducer

from order_events import OrderPlaced

from inventory_service.application.handle_order import HandleOrderHandler
from inventory_service.config import settings
from inventory_service.infrastructure.kafka.consumer import KafkaOrderConsumer
from inventory_service.infrastructure.kafka.producer import KafkaResultPublisher
from inventory_service.infrastructure.repositories.in_memory import InMemoryInventoryRepository

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

async def main() -> None:
    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, stop_event.set)
    loop.add_signal_handler(signal.SIGINT, stop_event.set)

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        enable_idempotence=True,
        acks="all",
    )
    await producer.start()
    log.info("kafka_producer_started")

    consumer = KafkaOrderConsumer()
    await consumer.start()
    log.info(
        "kafka_consumer_started",
        topic=settings.kafka_orders_topic,
        group=settings.kafka_consumer_group,
    )

    repo = InMemoryInventoryRepository(settings.initial_stock)
    result_publisher = KafkaResultPublisher(producer)
    handler = HandleOrderHandler(repo, result_publisher)

    log.info("inventory_service_ready", initial_stock=settings.initial_stock)

    try:
        async for msg in consumer:
            if stop_event.is_set():
                break
            try:
                event = OrderPlaced.model_validate_json(msg.value.decode())
                await handler.handle(event)
            except Exception as exc:
                log.error("message_processing_failed", error=str(exc), raw=msg.value.decode())
                await result_publisher.publish_to_dlq(msg.value)
            finally:
                await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()
        log.info("inventory_service_stopped")

if __name__ == "__main__":
    asyncio.run(main())