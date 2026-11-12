import asyncio
import json
import os
import logging
from aiokafka import AIOKafkaProducer
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://shop:shop@postgres-primary:5432/shop").replace("+asyncpg", "")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
BATCH_SIZE = 100

async def publish_outbox():
    conn = await asyncpg.connect(DATABASE_URL)
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        acks="all",
        enable_idempotence=True,
    )
    await producer.start()
    logger.info("Outbox Publisher started")
    
    try:
        while True:
            rows = await conn.fetch(
                "SELECT id, topic, event_id, payload FROM outbox WHERE published = FALSE ORDER BY created_at ASC LIMIT $1 FOR UPDATE SKIP LOCKED",
                BATCH_SIZE
            )
            if not rows:
                await asyncio.sleep(0.1)
                continue
            
            for row in rows:
                payload = row["payload"]
                if isinstance(payload, str):
                    payload = json.loads(payload)
                
                key = str(payload["user_id"]).encode() if "user_id" in payload else None
                
                await producer.send_and_wait(
                    row["topic"], 
                    value=json.dumps(payload).encode(), 
                    key=key
                )
                
                await conn.execute(
                    "UPDATE outbox SET published = TRUE, published_at = NOW() WHERE id = $1",
                    row["id"]
                )
                logger.info(f"✓ Published event {row['event_id']} to {row['topic']}")
                
    finally:
        await producer.stop()
        await conn.close()

if __name__ == "__main__":
    asyncio.run(publish_outbox())