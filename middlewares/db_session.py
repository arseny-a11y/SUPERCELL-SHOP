from typing import Any, Callable, Awaitable
from aiogram.types import TelegramObject
from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker


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