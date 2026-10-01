from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.models import User, PromoCode,PromoUsage
from database.queries import UserQueries,check_promocode
from aiogram.types import FSInputFile #работа с изображениями
from keyboards.reply import create_keyboard_menu
from keyboards.inline import keyboard_support,keyboard_profile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from payments.crypto_pay import CryptoPay
from config.config import settings


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

#активация промокода

class EnterPromoState(StatesGroup):
    waiting_for_code = State()

@user_router.callback_query(F.data == "enter_promocode")
async def enter_promocode_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EnterPromoState.waiting_for_code)

    await callback.message.answer("✨ Введите промокод: ")

@user_router.message(EnterPromoState.waiting_for_code)
async def waiting_for_code_state(message: Message, state: FSMContext, session: AsyncSession):

    promo_code = message.text.strip() if message.text else " "

    existing = await check_promocode(session, promo_code)

    if existing is None or existing.max_uses <= 0:
        await state.clear()
        return await message.answer("❌ Промокод не найден, либо уже активирован")

    user_id = message.from_user.id

    used_code = await session.scalar(select(PromoUsage).where(PromoUsage.promo_id == existing.id, PromoUsage.tg_id == user_id))

    if used_code:
        await state.clear()
        return await message.answer("⚠️ Вы уже активировали этот промокод!")

    user = await session.scalar(select(User).where(User.tg_id == user_id))

    if user is None:
        await state.clear()
        return await message.answer("❌ Пользовалель не найден в базе")

    
    existing.max_uses -= 1
    existing.current_uses += 1
    user.balance += existing.reward_amount


    create_promocode_usage = PromoUsage(
        promo_id=existing.id,
        tg_id=user_id
    )


    session.add(create_promocode_usage)
    await session.commit()
    await state.clear()

    await message.answer(
        f"✅ Промокод <code>{promo_code}</code> успешно активирован!\n\n"
        f"💰 Ваш баланс пополнен на <b>{existing.reward_amount:.2f} ₽</b>\n"
        f"🪙 Текущий баланс: <b>{user.balance:.2f} ₽</b>",
        parse_mode="HTML",
    )
