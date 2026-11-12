import asyncio
from sqlalchemy import text
from app.database import engine

async def seed_db():
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO users (id, email, name) 
            VALUES (1, 'test@example.com', 'Test User') 
            ON CONFLICT (id) DO NOTHING;
        """))

        await conn.execute(text("""
            INSERT INTO products (id, sku, name, price, stock, category) 
            VALUES (1, 'TEST-SKU-001', 'Test Product', 150.00, 100, 'Test') 
            ON CONFLICT (id) DO NOTHING;
        """))
        
    print("Тестовые данные успешно добавлены в базу данных")

if __name__ == "__main__":
    asyncio.run(seed_db())