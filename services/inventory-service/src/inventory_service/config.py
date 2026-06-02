from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_orders_topic: str = "orders"
    kafka_results_topic: str = "orders.results"
    kafka_dlq_topic: str = "orders.dlq"
    kafka_consumer_group: str = "inventory-service"
    initial_stock: dict[str, int] = {"item-1": 10, "item-2": 5, "item-3": 20}


settings = Settings()