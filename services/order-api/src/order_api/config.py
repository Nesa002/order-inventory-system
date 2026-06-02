from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_orders_topic: str = "orders"
    kafka_results_topic: str = "orders.results"
    kafka_dlq_topic: str = "orders.dlq"

settings = Settings()