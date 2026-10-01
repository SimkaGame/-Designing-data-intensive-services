import asyncio
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func
from faker import Faker

from app.database import async_session_factory
from app.models import User, Product, Order, OrderItem

fake = Faker("ru_RU")
random.seed(42)  # Воспроизводимость данных


CATEGORIES = ["Ноутбуки", "Смартфоны", "Наушники", "Клавиатуры", "Мыши", "Мониторы"]


async def seed_users(session, count: int = 1000) -> list[int]:
    """Создаёт count пользователей, возвращает их id."""
    users = []
    for i in range(count):
        user = User(
            email=f"user{i}@{fake.domain_name()}",
            name=fake.name(),
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365)),
        )
        users.append(user)
    session.add_all(users)
    await session.flush()
    return [u.id for u in users]


async def seed_products(session, count: int = 500) -> list[tuple[int, Decimal]]:
    """Создаёт count товаров, возвращает (id, price)."""
    products = []
    for i in range(count):
        category = random.choice(CATEGORIES)
        price = Decimal(str(round(random.uniform(500, 200000), 2)))
        product = Product(
            sku=f"SKU-{i:06d}",
            name=f"{category[:-1]} {fake.word().capitalize()} {fake.word().capitalize()}",
            description=fake.text(max_nb_chars=500),
            price=price,
            stock=random.randint(0, 1000),
            category=category,
        )
        products.append(product)
    session.add_all(products)
    await session.flush()
    return [(p.id, p.price) for p in products]


async def seed_orders(
    session,
    user_ids: list[int],
    products: list[tuple[int, Decimal]],
    count: int = 10000,
) -> None:
    """Создаёт count заказов с 1-5 позициями каждый."""
    statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
    weights = [0.10, 0.40, 0.20, 0.25, 0.05]  # Распределение статусов

    for i in range(count):
        user_id = random.choice(user_ids)
        created_at = datetime.now(timezone.utc) - timedelta(
            days=random.randint(0, 180),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        order = Order(
            user_id=user_id,
            status=random.choices(statuses, weights=weights)[0],
            total=Decimal("0"),
            created_at=created_at,
        )
        session.add(order)
        await session.flush()  # Получаем order.id

        # 1–5 позиций в заказе
        n_items = random.randint(1, 5)
        total = Decimal("0")
        chosen_products = random.sample(products, n_items)

        for product_id, unit_price in chosen_products:
            quantity = random.randint(1, 3)
            item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
            )
            session.add(item)
            total += unit_price * quantity

        order.total = total

        if (i + 1) % 1000 == 0:
            print(f"  Создано заказов: {i + 1}/{count}")


async def main():
    async with async_session_factory() as session:
        # Проверка: не наполнена ли уже БД
        count = await session.scalar(select(func.count(User.id)))
        if count > 0:
            print(f"⚠️  В БД уже {count} пользователей. Пропускаем наполнение.")
            print("   Для пересоздания: TRUNCATE users CASCADE;")
            return

        print("Создание пользователей...")
        user_ids = await seed_users(session, 1000)

        print("Создание товаров...")
        products = await seed_products(session, 500)

        print("Создание заказов...")
        await seed_orders(session, user_ids, products, 10000)

        await session.commit()
        print("✓ База данных наполнена")


if __name__ == "__main__":
    asyncio.run(main())