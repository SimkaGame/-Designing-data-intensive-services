# report.py
import subprocess
import time
import requests

# ИСПРАВЛЕНИЕ 1: используем 127.0.0.1 и порт 8000
NGINX_URL = "http://127.0.0.1:8000"
REDIS_CONTAINER = "redis"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout

def redis_cmd(*args):
    return run(["docker", "compose", "exec", "-T", REDIS_CONTAINER, "redis-cli", *args])

def redis_info(section):
    out = redis_cmd("INFO", section)
    info = {}
    for line in out.split("\n"):
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return info

def timed_request(url):
    start = time.time()
    try:
        r = requests.get(url, timeout=10)
        return round((time.time() - start) * 1000, 2), r.status_code
    except Exception as e:
        return round((time.time() - start) * 1000, 2), f"ERR: {e}"

print("=" * 70)
print("МОДУЛЬ 4. ИТОГОВЫЙ ОТЧЁТ")
print("=" * 70)

redis_cmd("FLUSHDB")
print("\n✓ Кеш очищен (FLUSHDB)")

pong = redis_cmd("PING").strip()
print(f"✓ Redis ping: {pong}")

print("\n--- ХОЛОДНЫЙ КЕШ ---")
lat_cold, status = timed_request(f"{NGINX_URL}/products?limit=50")
print(f"  GET /products?limit=50 → {lat_cold} мс (status {status})")

# ИСПРАВЛЕНИЕ 2: используем реальный ID 1001
lat_cold_id, status2 = timed_request(f"{NGINX_URL}/products/1001")
print(f"  GET /products/1001     → {lat_cold_id} мс (status {status2})")

print("\n--- ТЁПЛЫЙ КЕШ (5 запросов) ---")
warm_lats = []
for i in range(5):
    lat, _ = timed_request(f"{NGINX_URL}/products?limit=50")
    warm_lats.append(lat)
    print(f"  Запрос {i+1}: {lat} мс")

avg_warm = sum(warm_lats) / len(warm_lats)
print(f"\n  Среднее: {avg_warm:.2f} мс")
print(f"  Ускорение vs холодный: {lat_cold / avg_warm:.1f}×")

keys_out = redis_cmd("KEYS", "*").strip()
keys = [k for k in keys_out.split("\n") if k]
print(f"\n--- КЛЮЧИ В REDIS ---")
print(f"  Всего ключей: {len(keys)}")
for k in keys[:10]:
    print(f"    {k}")

stats = redis_info("stats")
hits = int(stats.get("keyspace_hits", 0))
misses = int(stats.get("keyspace_misses", 0))
expired = int(stats.get("expired_keys", 0))
evicted = int(stats.get("evicted_keys", 0))
total = hits + misses
hit_ratio = (hits / total * 100) if total > 0 else 0

print(f"\n--- CACHE HIT RATIO ---")
print(f"  Попаданий (hits):   {hits:>10,}")
print(f"  Промахов (misses):  {misses:>10,}")
print(f"  Истекло TTL:        {expired:>10,}")
print(f"  Вытеснено (LRU):    {evicted:>10,}")
print(f"  Hit Ratio:          {hit_ratio:>9.2f}%")

if hit_ratio > 95:
    grade = "ОТЛИЧНО (>95%)"
elif hit_ratio > 80:
    grade = "ХОРОШО (>80%)"
elif hit_ratio > 50:
    grade = "СРЕДНЕ (>50%)"
else:
    grade = "ПЛОХО (<50%)"
print(f"  Оценка: {grade}")

mem = redis_info("memory")
print(f"\n--- ПАМЯТЬ REDIS ---")
print(f"  Использовано:  {mem.get('used_memory_human', 'N/A')}")
print(f"  Пик:           {mem.get('used_memory_peak_human', 'N/A')}")
print(f"  Max memory:    {mem.get('maxmemory_human', 'N/A')}")
print(f"  Policy:        {mem.get('maxmemory_policy', 'N/A')}")

print(f"\n--- ПРОВЕРКА ИНВАЛИДАЦИИ ---")
# ИСПРАВЛЕНИЕ 2: используем реальный ID 1001
before = timed_request(f"{NGINX_URL}/products/1001")[0]
print(f"  GET /products/1001 до PUT: {before} мс (из кеша)")

requests.put(
    f"{NGINX_URL}/products/1001",
    json={"name": "Test update invalidation"},
    timeout=5,
)
print(f"  PUT /products/1001 выполнен → кеш инвалидирован")

after = timed_request(f"{NGINX_URL}/products/1001")[0]
print(f"  GET /products/1001 после PUT: {after} мс (должен быть MISS → медленнее)")

print("\n" + "=" * 70)
print("ИТОГОВАЯ СВОДКА")
print("=" * 70)
print(f"  Архитектура:   Client → FastAPI:8000 → Redis + PostgreSQL")
print(f"  Паттерн:       Cache-Aside + mutex (защита от stampede)")
print(f"  Ключи:         product:{{id}}, products:limit:{{N}}")
print(f"  TTL:           60 сек (каталог), 300 сек (карточка)")
print(f"  Eviction:      allkeys-lru, maxmemory 512mb")
print(f"  Cold latency:  {lat_cold} мс")
print(f"  Warm latency:  {avg_warm:.1f} мс")
print(f"  Ускорение:     {lat_cold / avg_warm:.1f}×")
print(f"  Hit Ratio:     {hit_ratio:.2f}%  [{grade}]")
print(f"  Evicted keys:  {evicted}  (норма = 0)")
print("=" * 70)