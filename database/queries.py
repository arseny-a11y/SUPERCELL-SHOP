from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Categories, Items
import math

class UserQueries():

    @staticmethod
    async def get_or_create_users(session: AsyncSession, tg_id: int, username: str | None, full_name: str):
        query = (select(User).filter(User.tg_id == tg_id))
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            user = User(tg_id=tg_id,username=username,full_name=full_name)
            session.add(user)
            await session.flush()
            print(f'user_id={tg_id} успешно добавлен в базу!')
        return user

class ProductsQueries():
    @staticmethod

    async def get_all_categories(session: AsyncSession):
        categories = (await session.scalars(select(Categories))).all()
        return categories

    async def get_product(session: AsyncSession, callback_data):
        items = (await session.scalars(select(Items).where(Items.category_id == callback_data.category_id, Items.is_sold.is_(False)))).all()
        return items
    
    #реализация пагинации
    async def get_items(session: AsyncSession,page: int, items_rep_page: int,category_id: int):
        total_items = int(await session.scalar(select(func.count(Items.id)).where(Items.category_id == category_id,Items.is_sold.is_(False)))) or 0

        total_page = max(1, math.ceil(total_items / items_rep_page))

        offset = (page - 1) * items_rep_page
        items = (await session.scalars(select(Items).where(Items.category_id == category_id, Items.is_sold.is_(False)).offset(offset).limit(items_rep_page))).all()

        return offset,total_page,items
class CreatedCategories():
    @staticmethod

    async def new_category(session: AsyncSession, name: str):
        category = Categories(name=name)
        session.add(category)
        await session.commit()