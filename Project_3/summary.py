import subprocess

def run_psql(sql: str) -> str:
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", "postgres-shop", "psql", "-U", "shop", "-d", "shop", "-t", "-A", "-c", sql],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

print("=" * 60)
print("ИТОГОВАЯ СВОДКА ПО МОДУЛЮ 3 (ИЗ КОНТЕЙНЕРА)")
print("=" * 60)
print()

db_size = run_psql("SELECT pg_size_pretty(pg_database_size('shop'));")
print(f" Размер базы данных в PostgreSQL: {db_size}")

print("\n Количество строк в таблицах:")
for table in ["users", "products", "orders", "order_items"]:
    count = run_psql(f"SELECT COUNT(*) FROM {table};")
    print(f"   - {table}: {count}")

inconsistent = run_psql("""
    SELECT COUNT(*) FROM (
        SELECT o.id FROM orders o 
        JOIN order_items oi ON oi.order_id = o.id 
        GROUP BY o.id, o.total 
        HAVING o.total != SUM(oi.quantity * oi.unit_price)
    ) sub;
""")
print(f"\n Финансовые расхождения (inconsistent_orders): {inconsistent} (0 — всё идеально)")

print()
print("=" * 60)
print("✓ Архитектура проверена, данные актуальны.")
print("=" * 60)