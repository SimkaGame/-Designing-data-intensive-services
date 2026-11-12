from locust import HttpUser, task, between
import random

class ShopUser(HttpUser):
    wait_time = between(0.5, 2)
    
    @task(5)
    def view_products(self):
        self.client.get("/products?limit=20")
        
    @task(1)
    def create_order(self):
        self.client.post("/orders", json={
            "user_id": 1,
            "email": f"load_{random.randint(1, 999)}@test.com",
            "items": [{"product_id": 1, "quantity": 1, "unit_price": 150.0}]
        })