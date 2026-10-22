# app/cache.py
import json
import redis.asyncio as redis
from typing import Any, Callable, Optional
import asyncio
import os

# ВАЖНО: используем 127.0.0.1 вместо localhost, чтобы избежать проблем с IPv6 на Windows
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_timeout=2,
    socket_connect_timeout=2,
    max_connections=50,
)

async def get_json(key: str) -> Optional[Any]:
    try:
        raw = await redis_client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        print(f"❌ ОШИБКА REDIS GET [{key}]: {e}")
        return None

async def set_json(key: str, value: Any, ttl: int = 60) -> None:
    try:
        await redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        print(f"❌ ОШИБКА REDIS SET [{key}]: {e}")

async def invalidate(key: str) -> None:
    try:
        await redis_client.delete(key)
    except Exception as e:
        print(f"❌ ОШИБКА REDIS DELETE [{key}]: {e}")

async def invalidate_pattern(pattern: str) -> None:
    try:
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor=cursor, match=f"{pattern}*", count=100)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break
    except Exception as e:
        print(f"❌ ОШИБКА REDIS SCAN: {e}")

async def cached(key: str, ttl: int, fetch_fn: Callable, lock_timeout: int = 10):
    cached_value = await get_json(key)
    if cached_value is not None:
        print(f"✅ КЕШ HIT: {key}")
        return cached_value
    
    print(f"⚠️ КЕШ MISS: {key} (идём в БД)")
    lock_key = f"lock:{key}"
    try:
        acquired = await redis_client.set(lock_key, "1", nx=True, ex=lock_timeout)
    except Exception as e:
        print(f"❌ ОШИБКА БЛОКИРОВКИ: {e}")
        acquired = True

    if not acquired:
        for _ in range(20):
            await asyncio.sleep(0.05)
            cached_value = await get_json(key)
            if cached_value is not None:
                return cached_value

    try:
        value = await fetch_fn()
        await set_json(key, value, ttl)
        return value
    finally:
        try:
            await redis_client.delete(lock_key)
        except Exception:
            pass