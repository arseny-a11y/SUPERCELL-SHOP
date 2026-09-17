from typing import Any, Callable, Awaitable
from aiogram.types import TelegramObject, User
from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from database.queries import UserQueries

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker) -> None:
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
            self, 
            handler: Callable[[TelegramObject, dict[str,Any]], Awaitable[Any]],
            event: TelegramObject, 
            data: dict[str, Any],) -> Any:
        
        async with self.session_pool() as session:
            #кладем сессию в словарь
            data['session'] = session
            #передаем данные на handler
            return await handler(event,data)

class UserDatabaseMiddleware(BaseMiddleware):
    async def __call__(
            self, 
            handler: Callable[[TelegramObject, dict[str,Any]], Awaitable[Any]],
            event: TelegramObject, 
            data: dict[str, Any],) -> Any:

        tg_user: User | None = data.get('event_from_user')

        if tg_user is None or tg_user.is_bot:
            return await handler(event,data)

        session: AsyncSession = data['session']

        data['user'] = await UserQueries.get_or_create_users(
            session=session,
            tg_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name
        )

        return await handler(event,data)