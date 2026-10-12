import random
from locust import HttpUser, task, between

class ShopUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def view_products(self):
        """Просмотр списка товаров (каталог)."""
        self.client.get("/products")

    @task(3)
    def view_product_detail(self):
        """Просмотр конкретного товара (ID от 1 до 500)."""
        product_id = random.randint(1, 500)
        self.client.get(f"/products/{product_id}")

    @task(2)
    def create_order(self):
        """Оформление заказа (основная нагрузка на БД и транзакции)."""
        payload = {
            "user_id": random.randint(1, 1000),
            "items": [
                {"product_id": random.randint(1, 500), "quantity": random.randint(1, 3)}
            ]
        }
        self.client.post("/orders/", json=payload)