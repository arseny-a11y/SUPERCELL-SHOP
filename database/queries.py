from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

class UserQueries():

    @staticmethod
    async def get_or_create_users(session: AsyncSession, tg_id: int, username: str | None, full_name: str):
        query = (select(User).filter(User.tg_id == tg_id))
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            user = User(tg_id=tg_id,username=username,full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f'user_id={tg_id} успешно добавлен в базу!')
        return user