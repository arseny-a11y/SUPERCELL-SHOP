from aiogram import Dispatcher, Bot
from aiogram.client.session.aiohttp import AiohttpSession # работа с proxy
import asyncio
import logging
from config.config import settings
from middlewares.middleware import DbSessionMiddleware, UserDatabaseMiddleware
from database.database import async_session_factory
from database.database import init_db
from handlers.user import user_router
from handlers.catalog import catalog_router
from handlers.admin import admin_router

async def main():
    session = AiohttpSession(proxy=settings.PROXY_URL)
    bot = Bot(settings.TOKEN,session=session)
    dp = Dispatcher()

    
    #инициализируем табилицы в базе
    await init_db()
    #подключаем middlewares
    dp.update.outer_middleware(DbSessionMiddleware(session_pool=async_session_factory))
    dp.update.outer_middleware(UserDatabaseMiddleware())

    #подключаем routers
    dp.include_router(catalog_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)    
    logging.basicConfig(level=logging.INFO)
 
    try:
        print('Бот запущен!')
        # Удаляем вебхуки и сбрасываем подвисшие апдейты
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    finally:
        # Корректно закрываем сессию соединений
        await bot.session.close()   

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Бот остановлен!')

    