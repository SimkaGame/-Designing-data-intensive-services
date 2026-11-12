import asyncio
import json
import os
import logging
from aiokafka import AIOKafkaConsumer
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://shop:shop@postgres-primary:5432/shop").replace("+asyncpg", "")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = "order.created"
GROUP_ID = "order-analytics"

async def process_order_created(event: dict, conn: asyncpg.Connection):
    event_id = event["event_id"]
    
    if await conn.fetchval("SELECT 1 FROM processed_events WHERE event_id = $1", event_id):
        logger.info(f"⏭ Event {event_id} already processed — skipping")
        return
    
    async with conn.transaction():
        await conn.execute(
            "INSERT INTO analytics (order_id, user_id, total) VALUES ($1, $2, $3) ON CONFLICT (order_id) DO NOTHING",
            event["order_id"], event["user_id"], event["total"]
        )
        await conn.execute(
            "INSERT INTO processed_events (event_id, topic) VALUES ($1, $2)",
            event_id, TOPIC
        )
    logger.info(f"Processed event {event_id} for order {event['order_id']}")

async def consume_orders():
    conn = await asyncpg.connect(DATABASE_URL)
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    await consumer.start()
    logger.info(f"Kafka Consumer started, topic={TOPIC}, group={GROUP_ID}")
    
    try:
        async for msg in consumer:
            try:
                event = json.loads(msg.value.decode())
                logger.info(f"← partition={msg.partition} offset={msg.offset} order_id={event['order_id']}")
                await process_order_created(event, conn)
                await consumer.commit()
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    finally:
        await consumer.stop()
        await conn.close()

if __name__ == "__main__":
    asyncio.run(consume_orders())