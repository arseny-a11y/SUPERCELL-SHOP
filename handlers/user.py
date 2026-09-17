from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.models import User
from database.queries import UserQueries
from aiogram.types import FSInputFile #работа с изображениями
from keyboards.reply import create_keyboard_menu
from keyboards.inline import keyboard_support
from keyboards.inline import keyboard_profile

user_router = Router()

@user_router.message(CommandStart())
async def start_command(message: Message, user: User):

    photo = FSInputFile('images/menu.png')

    text = (
        f"👋 <b>{message.from_user.first_name}</b>, приветствуем тебя!\n\n"
        "🎉 <b>Добро пожаловать в SUP SHOP!</b>\n"
        "У нас ты найдешь лучший выбор аккаунтов и цифровых товаров Supercell.\n\n"
        "😉 Заглядывай в каталог и выбирай самые топовые товары! С любовью, SUP SHOP 🧡"
    )
    await message.answer_photo(photo=photo,caption=text,parse_mode='HTML',reply_markup=create_keyboard_menu())


#обработка информации о магазине
@user_router.message(F.text == "ℹ️ О SUP SHOP")
async def information_shop(message: Message):
    photo = FSInputFile('images/menu.png')

    text = (
        "👋 <b>Приветствуем в SUP SHOP!</b>\n\n"
        "❤️ Мы рады предложить вам широкий ассортимент товаров по конкурентным ценам. 🛍 Наша бизнес-модель основана на приобретении дорогостоящих материалов 💎 и их реализации по более доступным ценам 💰 благодаря работе с большой аудиторией. 👨‍👩‍👧‍👦\n\n"
        "📅 Дата основания магазина: 04.09.2026."
    )
    await message.answer_photo(photo=photo,caption=text,parse_mode='HTML')


#обработка запроса на контакты поддержки
@user_router.message(F.text == "🆘 Поддержка")
async def support_shop(message: Message):
    photo = FSInputFile('images/support.png')

    text = (
        "🤝 В нашем боте вы всегда можете рассчитывать на оперативную поддержку! Возникли вопросы при покупке, оплате или получении товара? Пишите нам! Мы ответим максимально быстро и решим вашу проблему\n\n"
        "🚨 Внимание! Мы никогда не пишем первыми. Если вам кто-то пишет от имени нашего бота или службы поддержки — это мошенники. Будьте осторожны!\n\n"
        "✍️ Связаться с поддержкой: @Gemaglobin"
    )
    await message.answer_photo(photo=photo,caption=text,reply_markup=keyboard_support())


#обработка запроса на статистику профиля
@user_router.message(F.text == "Профиль 👤")
async def user_profile(message: Message, user: User):
    photo = FSInputFile('images/profile.png')

    registered_at = user.registered_at.strftime("%d.%m.%Y")
    username = user.username if user.username else 'Отсутсвует'
    text = (
        f"📍<b>ID</b>: {user.tg_id}\n"
        f"💾 <b>Имя</b>: @{username}\n"
        f"💵 <b>Баланс</b>: {user.balance}\n"
        f"🕑 <b>Дата регистрации</b>: {registered_at}\n"
    )
    await message.answer_photo(photo=photo,caption=text,reply_markup=keyboard_profile(),parse_mode='HTML')