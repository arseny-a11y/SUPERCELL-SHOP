from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from database.queries import UserQueries
from aiogram.types import FSInputFile #работа с изображениями

user_router = Router()

@user_router.message(CommandStart())
async def start_command(message: Message, session: AsyncSession):

    user = await UserQueries.get_or_create_users(
        session=session,
        tg_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    photo = FSInputFile('images/menu.png')
    text = (
        f"👋 <b>{message.from_user.first_name}</b>, приветствуем тебя!\n\n"
        "🎉 <b>Добро пожаловать в SUP SHOP!</b>\n"
        "У нас ты найдешь лучший выбор аккаунтов и цифровых товаров Supercell.\n\n"
        "😉 Заглядывай в каталог и выбирай самые топовые товары! С любовью, SUP SHOP 🧡"
    )
    await message.answer_photo(photo=photo,caption=text,parse_mode='HTML')
