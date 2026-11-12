from celery import Celery
from celery.schedules import crontab
import os
import asyncio
import asyncpg

celery_app = Celery(
    "shop",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/1"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/2"),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=10,
    task_max_retries=3,
)

@celery_app.task(bind=True, max_retries=3, name="app.tasks.send_email")
def send_email(self, to: str, subject: str, body: str):
    try:
        print(f"Sending email to {to}: {subject}")
        import time
        time.sleep(0.1)
        print(f"✓ Email sent to {to}")
        return {"status": "sent", "to": to}
    except Exception as exc:
        print(f"✗ Error sending email: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="app.tasks.cleanup_old_events")
def cleanup_old_events():
    async def _cleanup():
        db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://shop:shop@postgres-primary:5432/shop").replace("+asyncpg", "")
        conn = await asyncpg.connect(db_url)
        try:
            result = await conn.execute("DELETE FROM processed_events WHERE processed_at < NOW() - INTERVAL '7 days'")
            print(f"Cleaned up old events: {result}")
        finally:
            await conn.close()
    asyncio.run(_cleanup())

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=0, minute=0), cleanup_old_events.s())