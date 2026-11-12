import uuid
import time
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Product, Order, OrderItem, Outbox, Analytics
from app.cache import cached, invalidate, invalidate_pattern
from app.schemas import OrderCreate, OrderResponse
from app.tasks import send_email

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
    
    await invalidate(f"product:{product_id}")
    await invalidate_pattern("products:limit:")
    
    return {"status": "updated"}

@app.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate, db: AsyncSession = Depends(get_db)):
    total = sum(item.quantity * item.unit_price for item in order_data.items)
    order = Order(user_id=order_data.user_id, status="pending", total=total)
    db.add(order)
    await db.flush()
    
    for item_data in order_data.items:
        item = OrderItem(
            order_id=order.id, 
            product_id=item_data.product_id, 
            quantity=item_data.quantity, 
            unit_price=item_data.unit_price
        )
        db.add(item)
    
    event = {
        "event_id": str(uuid.uuid4()),
        "order_id": order.id,
        "user_id": order.user_id,
        "total": float(order.total),
        "status": "created",
        "timestamp": time.time(),
    }
    db.add(Outbox(topic="order.created", event_id=event["event_id"], payload=event, published=False))

    if order_data.email:
        send_email.delay(
            to=order_data.email,
            subject=f"Заказ #{order.id} создан",
            body=f"Сумма: {order.total} руб. Спасибо за покупку!"
        )
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total=float(order.total),
        created_at=order.created_at
    )

@app.get("/analytics/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.count(Analytics.id).label("total_orders"), 
            func.sum(Analytics.total).label("total_revenue")
        )
    )
    row = result.one()
    return {
        "total_orders": row.total_orders or 0,
        "total_revenue": float(row.total_revenue or 0)
    }