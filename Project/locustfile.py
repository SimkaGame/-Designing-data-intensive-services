from locust import HttpUser, task, between

class ShopUser(HttpUser):
    """
    Имитация пользователя интернет-магазина.
    Пользователь выполняет задачи с паузой 1-3 секунды между ними.
    """
    wait_time = between(1, 3)

    @task(5)  # Вес 5 — самая частая задача
    def view_products(self):
        """Просмотр списка товаров."""
        self.client.get("/products")

    @task(3)  # Вес 3 — средняя частота
    def view_product(self):
        """Просмотр конкретного товара."""
        product_id = 1  # В реальном тесте можно рандомизировать
        self.client.get(f"/products/{product_id}")

    @task(1)  # Вес 1 — редкая задача
    def health_check(self):
        """Проверка здоровья (редко в реальной жизни)."""
        self.client.get("/health")