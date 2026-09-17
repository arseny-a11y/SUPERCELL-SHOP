from database.database import create_async_engine, async_session_factory
from database.models import Categories, Items
import asyncio

async def create_database():
    async with async_session_factory() as session:
        brawl = Categories(name='Brawl Stars')
        clash = Categories(name='Clash Royal')

        session.add_all([brawl,clash])
        await session.flush()

        products = [
            Items(
                category_id=brawl.id,
                title="Аккаунт 25k кубков + Леон",
                description="Полная перепривязка почты, 55 бойцов, 12 гиперзарядов.",
                price=1499.00,
                data="login:pass_brawl_25k | Mail: mail@example.com:secret",
                is_sold=False,
            ),
            Items(
                category_id=brawl.id,
                title="Стартовый аккаунт 5k кубков",
                description="Отличный старт для новичка, есть немного гемов.",
                price=299.00,
                data="login:pass_brawl_5k",
                is_sold=False,
            ),
            Items(
                category_id=clash.id,
                title="15 Арена + 3 Эволюции",
                description="Топ колода прокачана на максимум, смена ника бесплатная.",
                price=890.00,
                data="clash_account_creds_here",
                is_sold=False,
            ),
        ]
        

        session.add_all(products)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(create_database())