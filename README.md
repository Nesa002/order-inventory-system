# Nenad Beric

# order-inventory-system

Event-driven order and inventory management system built with two independent Python microservices communicating via Kafka.

## Architecture

```
Client
  │  POST /orders {"orderId", "itemId", "quantity"}
  ▼
┌─────────────┐                          ┌───────────────────┐
│  Order API  │ ──── OrderPlaced ──────► │                   │
│  (FastAPI)  │      orders topic        │       Kafka       │
└─────────────┘                          │                   │
      │                                  └────────┬──────────┘
      │ 202 Accepted                              │ consume
      ▼                                           ▼
   Client                             ┌──────────────────────┐
                                      │  Inventory Service   │
                                      │  (consumer loop)     │
                                      └──────────────────────┘
                                                │
                                                │ OrderResult
                                                ▼
                                      ┌───────────────────┐
                                      │       Kafka       │
                                      │  orders.results   │
                                      │  orders.dlq       │
                                      └───────────────────┘
```

The Order API publishes an event and returns `202 Accepted` immediately — it does not wait for inventory processing. The Inventory Service consumes events asynchronously, checks stock, and publishes results back to Kafka on `orders.results`.

## Key Design Decisions

- **Fire-and-forget / 202 Accepted** — the Order API returns as soon as Kafka confirms the event is durably stored. The client does not wait for inventory processing. `202` (not `200`) signals that work is ongoing.
- **Idempotent Kafka producer** (`enable_idempotence=True`, `acks="all"`) — if the Order API crashes after publishing but before returning, the client retries with the same `orderId` and Kafka deduplicates at the broker level.
- **Manual offset commit** — the Inventory Service commits its Kafka offset only *after* successfully processing a message. A crash mid-processing causes the message to replay on restart (at-least-once delivery).
- **Consumer idempotency** — `processed_order_ids: set[str]` guards against replayed messages. The handler skips any `orderId` it has already seen.
- **`item_id` as Kafka partition key** — all events for the same item always land on the same partition. In a multi-instance deployment, one inventory instance owns each item, keeping per-item in-memory state consistent without coordination.
- **Shared event schema package** — `OrderPlaced` and `OrderResult` Pydantic models live in `shared/` and are installed as a local package in both services. No schema duplication, no drift.
- **Dead letter queue** — messages that fail processing are published to `orders.dlq` before the offset is committed. The service moves on rather than blocking on a poison message.
- **Graceful shutdown** — the Inventory Service handles `SIGTERM` (sent by Docker on `compose down`), finishes the current message, commits its offset, then exits cleanly.

## Running

**Requirements:** Docker with Docker Compose

```bash
docker compose up --build -d
```

Startup order is enforced: Kafka must pass its healthcheck before `kafka-init` creates the topics, and both services wait for `kafka-init` to complete before starting.

Check everything is up:
```bash
docker compose ps
```

Watch inventory logs in real time:
```bash
docker compose logs -f inventory-service
```

## Testing

**1. Successful reservation**
```bash
curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d "{\"orderId\":\"1\",\"itemId\":\"item-1\",\"quantity\":3}"
```
Order API returns `{"orderId":"1","status":"accepted"}`. Inventory logs:
```json
{"order_id": "1", "item_id": "item-1", "quantity": 3, "status": "reserved", "event": "order_processed"}
```

**2. Rejected — insufficient stock**
```bash
curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d "{\"orderId\":\"2\",\"itemId\":\"item-1\",\"quantity\":99}"
```
Inventory logs:
```json
{"order_id": "2", "status": "rejected", "reason": "insufficient stock for item-1", "event": "order_processed"}
```

**3. Idempotency — duplicate order ID**
```bash
curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d "{\"orderId\":\"1\",\"itemId\":\"item-1\",\"quantity\":3}"
```
Inventory logs:
```json
{"order_id": "1", "event": "order_skipped_duplicate"}
```

**4. Drain stock completely**
```bash
curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d "{\"orderId\":\"3\",\"itemId\":\"item-2\",\"quantity\":5}"
curl -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d "{\"orderId\":\"4\",\"itemId\":\"item-2\",\"quantity\":1}"
```
Order 3 → `reserved` (stock was 5, now 0). Order 4 → `rejected`.

**5. Health check**
```bash
curl http://localhost:8000/health
```
Returns `{"status":"ok"}`.

**Inspect Kafka topics directly:**
```bash
# See all OrderResult events
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders.results --from-beginning

# Confirm DLQ is empty
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders.dlq --from-beginning --max-messages 1 --timeout-ms 3000
```

## Stopping

```bash
docker compose down
```

## Known Limitations

- **In-memory stock** — inventory state is not persisted. Restarting the inventory service resets stock to the seeded values.
- **Single instance** — the in-memory stock dict is process-local. Running multiple inventory service instances would cause each to maintain its own diverging view of stock levels.
- **In-memory idempotency set** — `processed_order_ids` resets on restart, so replayed messages from before the restart will be processed again.

## Production Upgrade Path

The current implementation is intentionally scoped to demonstrate integration quality over operational completeness. Natural next steps would be:

- Replace the in-memory stock store with **Redis**, enabling multiple inventory instances to share state
- Replace the idempotent producer with the **Outbox Pattern** — write the order and the outbox entry in a single database transaction, then relay to Kafka, eliminating the dual-write risk entirely
- Add **OpenTelemetry** distributed tracing to thread `order_id` through spans across both services, and **Prometheus** metrics for consumer lag and DLQ depth