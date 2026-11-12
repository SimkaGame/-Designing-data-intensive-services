import asyncio
import httpx
import json

async def check_edu_flow():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        print("Создаем тестовый заказ...")
        
        resp = await client.post("/orders", json={
            "user_id": 1,
            "email": "auto_test@example.com",
            "items": [{"product_id": 1, "quantity": 2, "unit_price": 150.0}]
        })
        
        if resp.status_code != 201:
            print(f"Ошибка создания заказа: {resp.status_code} - {resp.text}")
            return
            
        order = resp.json()
        print(f"Заказ создан! ID: {order['id']}, Сумма: {order['total']}")
        
        print("Ожидаем обработку события...")
        await asyncio.sleep(3)
        
        print("Проверяем аналитику...")
        analytics = await client.get("/analytics/summary")
        data = analytics.json()
        
        print(f"Total Orders: {data['total_orders']}")
        print(f"Total Revenue: {data['total_revenue']}")
        
        if data['total_orders'] > 0:
            print("УСПЕХ! EDA-цикл работает корректно!")
        else:
            print("ВНИМАНИЕ: Заказ создан, но аналитика пуста.")
            print("Проверьте логи: docker compose logs outbox-publisher kafka-consumer")

if __name__ == "__main__":
    asyncio.run(check_edu_flow())