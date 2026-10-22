# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Product
from app.cache import cached, invalidate, invalidate_pattern

app = FastAPI(title="Highload Shop API")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/products")
async def list_products(limit: int = 100, db: AsyncSession = Depends(get_db)):
    cache_key = f"products:limit:{limit}"
    
    async def fetch():
        result = await db.execute(select(Product).limit(limit))
        products = result.scalars().all()
        return [
            {
                "id": p.id, "sku": p.sku, "name": p.name,
                "price": str(p.price), "stock": p.stock, "category": p.category,
            }
            for p in products
        ]
    
    return await cached(cache_key, ttl=60, fetch_fn=fetch)

@app.get("/products/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    cache_key = f"product:{product_id}"
    
    async def fetch():
        product = await db.get(Product, product_id)
        if not product:
            return None
        return {
            "id": product.id, "sku": product.sku, "name": product.name,
            "price": str(product.price), "stock": product.stock,
            "category": product.category, "description": product.description,
        }
    
    result = await cached(cache_key, ttl=300, fetch_fn=fetch)
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result

@app.put("/products/{product_id}")
async def update_product(product_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in data.items():
        setattr(product, key, value)
    await db.commit()
    
    # Инвалидация кеша при изменении
    await invalidate(f"product:{product_id}")
    await invalidate_pattern("products:limit:")
    
    return {"status": "updated"}