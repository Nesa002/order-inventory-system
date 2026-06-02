from aiokafka import AIOKafkaProducer

from order_events import OrderResult

from inventory_service.application.ports import ResultPublisher
from inventory_service.config import settings

class KafkaResultPublisher(ResultPublisher):
    def __init__(self, producer: AIOKafkaProducer) -> None:
        self._producer = producer

    async def publish(self, result: OrderResult) -> None:
        await self._producer.send_and_wait(
            settings.kafka_results_topic,
            value=result.model_dump_json().encode(),
            key=result.order_id.encode(),
        )

    async def publish_to_dlq(self, raw_message: bytes) -> None:
        await self._producer.send_and_wait(
            settings.kafka_dlq_topic,
            value=raw_message,
        )