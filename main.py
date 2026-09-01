from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import FSInputFile
from aiogram.client.session.aiohttp import AiohttpSession
import asyncio
import logging
from config.config import settings

session = AiohttpSession(proxy=settings.PROXY_URL)
bot = Bot(settings.TOKEN,session=session)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_comand(message: Message):

    photo = FSInputFile('image/menu.png')
    text = (
        f"👋 <b>{message.from_user.first_name}</b>, приветствуем тебя!\n\n"
        "🎉 <b>Добро пожаловать в SUP SHOP!</b>\n"
        "У нас ты найдешь лучший выбор аккаунтов и цифровых товаров Supercell.\n\n"
        "😉 Заглядывай в каталог и выбирай самые топовые товары! С любовью, SUP SHOP 🧡"
    )
    await message.answer_photo(photo=photo,caption=text,parse_mode='HTML')

async def main():
    try:
        logging.basicConfig(level=logging.INFO)
        print('Бот запущен!')
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        print('Бот остановлен!')

if __name__ == '__main__':
    asyncio.run(main())

    