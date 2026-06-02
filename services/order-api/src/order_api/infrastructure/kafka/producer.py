from aiokafka import AIOKafkaProducer

from order_api.application.ports import EventPublisher
from order_api.config import settings
from order_events import OrderPlaced

class KafkaEventPublisher(EventPublisher):
    def __init__(self, producer: AIOKafkaProducer) -> None:
        self._producer = producer
        self._topic = settings.kafka_orders_topic

    async def publish(self, event: OrderPlaced) -> None:
        await self._producer.send_and_wait(
            self._topic,
            value=event.model_dump_json().encode(),
            key=event.item_id.encode(),
        )