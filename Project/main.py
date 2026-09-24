from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="Highload Shop API",
    description="Базовый сервис интернет-магазина для нагрузочного тестирования",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Корневой эндпоинт — имитация главной страницы."""
    return {
        "service": "highload-shop",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Эндпоинт проверки здоровья сервиса."""
    return {"status": "healthy"}

@app.get("/products")
async def list_products():
    """Имитация списка товаров."""
    return {
        "products": [
            {"id": 1, "name": "Ноутбук", "price": 89990},
            {"id": 2, "name": "Смартфон", "price": 49990},
            {"id": 3, "name": "Наушники", "price": 12990}
        ],
        "total": 3
    }

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Имитация получения товара по ID."""
    return {
        "id": product_id,
        "name": f"Товар #{product_id}",
        "price": 10000 + product_id * 1000
    }