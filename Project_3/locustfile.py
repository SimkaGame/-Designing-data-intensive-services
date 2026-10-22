from locust import HttpUser, task, between

class ShopUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Небольшая пауза между запросами

    @task(3)
    def get_products_list(self):
        # 3 из 4 запросов будут к списку товаров
        self.client.get("/products?limit=50")

    @task(1)
    def get_product_detail(self):
        # 1 из 4 запросов будет к конкретному товару
        self.client.get("/products/1001")