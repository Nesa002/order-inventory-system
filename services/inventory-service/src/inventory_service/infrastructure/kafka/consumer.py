from aiokafka import AIOKafkaConsumer

from inventory_service.config import settings

class KafkaOrderConsumer:
    def __init__(self) -> None:
        self._consumer = AIOKafkaConsumer(
            settings.kafka_orders_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )

    async def start(self) -> None:
        await self._consumer.start()

    async def stop(self) -> None:
        await self._consumer.stop()

    async def commit(self) -> None:
        await self._consumer.commit()

    def __aiter__(self):
        return self._consumer.__aiter__()