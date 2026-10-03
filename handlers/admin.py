from aiogram.filters import BaseFilter, Command
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from config.config import settings
from keyboards.reply import admin_menu 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func, delete, update
from database.models import Categories, Items, User, Orders, PromoCode, PromoUsage, SubCategories
from keyboards.inline import category_admin, keyboard_categories, cancel_mailing_kb, generation_code_kb, sub_category_admin
from database.queries import CreatedCategories, check_promocode
from decimal import Decimal, InvalidOperation
from datetime import datetime, time
from config.config import settings
import asyncio
import string
import secrets
import io


admin_router = Router()
ADMIN_ID = [settings.ADMIN_ID]

class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        return event.from_user.id in ADMIN_ID

admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())

@admin_router.message(Command("admin"))
async def admin_command(message: Message):
    await message.answer('Панель администратора открыта🫡',reply_markup=admin_menu())

#FSM состояние для загрузки товаров 
class AdminUploadItems(StatesGroup):
    waiting_for_category = State()
    waiting_for_sub_category = State()
    waiting_for_file = State()

class CreateCategory(StatesGroup):
    waiting_for_name = State()

class CreateSubCategory(StatesGroup):
    waiting_for_name = State()

#FSM состояние данных промокода
class PromoCodeState(StatesGroup):
    waiting_for_code = State()
    waiting_for_max_uses = State()
    waiting_for_amount = State()

#FSM состояние для редактирования товаров
class EditProductState(StatesGroup):
    waiting_for_data = State()
    waiting_for_price = State()


@admin_router.message(F.text == "📥 Загрузить (.txt) файл товаров")
async def upload_items(message: Message, session: AsyncSession, state: FSMContext):
    
    categories = (await session.scalars(select(Categories))).all()
    is_admin = (
        message.from_user.id == ADMIN_ID
    )
    if not categories:
        return await message.answer("Создайте хоть одну категорию!",reply_markup=keyboard_categories(categories,is_admin))

    
    await state.set_state(AdminUploadItems.waiting_for_category)
    await message.answer("Выберите категорию, в которую будут загружены товары:", reply_markup=category_admin(categories))

@admin_router.callback_query(AdminUploadItems.waiting_for_category, F.data.startswith("admin_cat"))
async def category_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    category_id = int(callback.data.split(":")[-1])

    await state.set_state(AdminUploadItems.waiting_for_sub_category)

    sub_category = (await session.scalars(select(SubCategories).where(SubCategories.category_id == category_id))).all()
    if not sub_category:
        await state.clear()
        return await callback.answer("⚠️ Подкатегория не найдена", show_alert=True)
        
    await callback.message.edit_text(
        "Категория выбрана.\n\n"
        "Выберите подкатегорию:",
        reply_markup=sub_category_admin(sub_category)
    )

    await callback.answer()

@admin_router.callback_query(AdminUploadItems.waiting_for_sub_category, F.data.startswith("admin_sub_cat"))
async def sub_category_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    sub_category_id = int(callback.data.split(":")[-1])
    await state.update_data(sub_category_id=sub_category_id)

    await state.set_state(AdminUploadItems.waiting_for_file)

    await callback.message.edit_text(
        "📂 <b>Подкатегория выбрана.</b>\n\n"
        "Отправьте <b>.txt</b> файл со списком товаров документом.\n\n"
        "Формат каждой строки:\n"
        "<code>Название | Описание | Цена_продажи | Себестоимость | Данные_товара</code>\n\n"
        "<i>Пример:</i>\n"
        "<code>TikTok RU | Отлега 30д | 45.0 | 20.0 | login:pass:mail</code>",
        parse_mode="HTML",
    )

@admin_router.message(AdminUploadItems.waiting_for_file, F.document)
async def upload_items(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if not message.document.file_name.endswith(".txt"):
        return await message.answer("❌ Отправьте файл с расширением (.txt)")

    data_fsm = await state.get_data()
    document = message.document
    file_in_io = io.BytesIO()

    await bot.download(document,destination=file_in_io)

    file_in_io.seek(0)

    try:
        content: str = file_in_io.read().decode("utf-8")
    except UnicodeDecodeError:
       return await message.answer("❌ Ошибка: кодировка файла должна быть UTF-8.") 

    products = []

    lines = [line.strip() for line in content.splitlines() if line.strip()] 
    if not lines:
        return await message.answer("❌ Ошибка: файл пуст")

    for num, line in enumerate(lines,start=1):
        data_account = [d.strip() for d in line.split("|")]

        if len(data_account) != 5:
            return await message.answer(f"❌ Ошибка: в строке {num}: ожидалось 5 полей через '|'")
        
        title, desc, price, purchase_price, data = data_account

        try:
            clean_price = Decimal(price.replace(",", "."))
            clean_purchase_price = Decimal(purchase_price.replace(",", "."))
        except InvalidOperation:
            return await message.answer(f"❌ Ошибка: Цена не является числом в строке {num}")

        products.append(
            Items(
                 category_id=data_fsm["sub_category_id"],
                 title=title,
                 description=desc,
                 price=clean_price,
                 purchase_price=clean_purchase_price,
                 data=data,
                 is_sold=False
            )
        )
    session.add_all(products)
    await session.commit() 

    await state.clear()   
    await message.answer(f"✅ Успешно добавлено товаров: <b>{len(products)}</b> шт.", parse_mode="HTML")




@admin_router.callback_query(F.data == "admin_cancel_upload")
async def cancel_upload(callback: CallbackQuery, state: FSMContext):
   await state.clear()
   await callback.message.edit_text("Загрузка отменена ❌")
   await callback.answer()


#Статистика продаж
@admin_router.message(F.text == "📊 Статистика")
async def sales_stats(message: Message, session: AsyncSession):
    
    #дата 00-00 сегодняшнего числа
    time_start = datetime.combine(datetime.now().date(), time.min)

    #кол-во юзеров в боте
    all_user_in_bot = await session.scalar(select(func.count(User.id))) or 0 
    #кол-во юзеров в боте за сегодня
    users_for_day = await session.scalar(select(func.count(User.id)).where(User.registered_at >= time_start)) or 0
    #баланс на руках у юзеров
    users_balance = await session.scalar(select(func.sum(User.balance))) or 0

    #всего продано товаров за все время
    all_salles_count = await session.scalar(select(func.count(Orders.id))) or 0
    #куплено товаров за сегодня 
    salles_for_day = await session.scalar(select(func.count(Orders.id)).where(Orders.purchased_at >= time_start)) or 0
    # кол-во товаров в наличии
    num_items_stock = await session.scalar(select(func.count(Items.id)).where(Items.is_sold.is_(False))) or 0

    #выручка всего
    total_revenue = await session.scalar(select(func.sum(Orders.price))) or 0
    #выручка за сегодня
    revenue_for_day = await session.scalar(select(func.sum(Orders.price)).where(Orders.purchased_at >= time_start)) or 0

    #чистыми за все время
    total_cost = await session.scalar(select(func.sum(Orders.purchase_price))) or 0
    clean_money = total_revenue - total_cost
    #чистыми за сегодня
    cost_for_day = await session.scalar(select(func.sum(Orders.purchase_price)).where(Orders.purchased_at >= time_start)) or 0
    clean_money_for_day = revenue_for_day - cost_for_day

    text = (
        "📊 **𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦 | Панель управления**\n\n"
        "👥 **Пользователи:**\n"
        f"├ Всего в боте: `{all_user_in_bot}` чел.\n"
        f"├ Новых за сегодня: `+{users_for_day}` чел.\n"
        f"└ Баланс на руках у юзеров: `{users_balance:.2f} ₽`\n\n"
        "📦 **Продажи и склад:**\n"
        f"├ Всего продано: `{all_salles_count}` шт.\n"
        f"├ Куплено сегодня: `{salles_for_day}` шт.\n"
        f"└ В наличии товаров: `{num_items_stock}` шт.\n\n"
        "💰 **Финансы:**\n"
        f"├ Выручка (всего): `{total_revenue:.2f} ₽`\n"
        f"├ Выручка за сегодня: `{revenue_for_day:.2f} ₽`\n"
        f"└ Чистыми за все время: `{clean_money:.2f} ₽`\n"
        f"└ Чистыми за сегодня: `{clean_money_for_day:.2f} ₽`"
    )

    await message.answer(text=text,parse_mode="Markdown")


#управление товарами
@admin_router.message(F.text == "📦 Управление товарами")
async def product_managment(message: Message, session: AsyncSession):
    is_admin = (
        message.from_user.id == ADMIN_ID
    )
    all_categories = await session.scalars(select(Categories))

    await message.answer(text="Выберите категорию для управления 📦", reply_markup=keyboard_categories(all_categories,is_admin))

#удаление категории
@admin_router.callback_query(F.data.startswith("del_cat"))
async def delete_category(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split(":")[-1])

    query = (select(Categories).where(Categories.id == cat_id))
    result = await session.execute(query)
    category = result.scalar_one_or_none()

    if not category:
        return await callback.answer("Категория уже удалена или не найдена.", show_alert=True)

    await session.delete(category)
    await session.commit()

    await callback.answer("Категория успешно удалена!")
    await callback.message.edit_text(f"✅ Категория #{cat_id} удалена.")

#удаление подкатегории
@admin_router.callback_query(F.data.startswith("delete_sub_cat"))
async def delete_sub_category(callback: CallbackQuery, session: AsyncSession):
    sub_category_id = int(callback.data.split(":")[-1])

    query = select(SubCategories).where(SubCategories.id == sub_category_id)
    result = await session.execute(query)
    sub_category = result.scalar_one_or_none()

    if not sub_category:
        return await callback.answer("Категория уже удалена или не найдена.", show_alert=True)

    await session.delete(sub_category)
    await session.commit()

    await callback.answer("Подкатегория успешно удалена!")
    await callback.message.edit_text(f"✅ Подкатегория #{sub_category_id} удалена.")
    

#ловит callback: admin_delete_item, для удаления конкретного товара
@admin_router.callback_query(F.data.startswith("admin_delete_item"))
async def delete_item(callback: CallbackQuery, session: AsyncSession):
    item_id = int(callback.data.split(":")[-1])

    del_item = (
        delete(Items).
        where(Items.id == item_id,Items.is_sold.is_(False))
    )
    result = await session.execute(del_item)
    await session.commit()

    if result.rowcount == 0:
        await callback.answer(
        "⚠️ Товар не найден или уже был куплен!", show_alert=True
    )

    else:
        await callback.answer("✅ Товар успешно удалён!", show_alert=True)
        await callback.message.edit_text("🗑 Товар был удалён из категории.")


#создание категории
@admin_router.callback_query(F.data == "create_category")
async def created_category_button(callback: CallbackQuery,state: FSMContext):

    await state.set_state(CreateCategory.waiting_for_name)
    await callback.message.edit_text("💬 Введите название категории: ")
    await callback.answer()


@admin_router.message(CreateCategory.waiting_for_name)
async def created_category_fsm(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text.strip() if message.text else ""

    if not text:
        return await message.answer("❌ Название категории должно быть строкой")
    
    category_name = text
    
    await CreatedCategories.new_categories(session, category_name)

    await message.answer(f"✅ Категория «{category_name}» создана!")
    await state.clear()


#создание подкатегорий
@admin_router.callback_query(F.data.startswith("create_sub_cat"))
async def create_sub_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession):

    category_id = int(callback.data.split(":")[-1])
    await state.update_data(category_id=category_id)

    await state.set_state(CreateSubCategory.waiting_for_name)

    await callback.message.edit_text("💬 Введите название подкатегории: ")
    await callback.answer()

@admin_router.message(CreateSubCategory.waiting_for_name)
async def created_sub_category_fsm(message: Message, state: FSMContext, session: AsyncSession):

    
    text = message.text.strip() if message.text else ""

    if not text:
        return await message.answer("❌ Название подкатегории должно быть строкой")

    data = await state.get_data()
    category_id = data.get("category_id")

    if not category_id:
        await state.clear()
        return await message.answer(
            "⚠️ Ошибка сессии: ID категории утерян. Попробуйте снова."
        )
    
    sub_category_name = text
  
    await CreatedCategories.new_sub_categories(session, sub_category_name,category_id)
    
    await state.clear()

    await message.answer(
        f"✅ Подкатегория <b>{text}</b> успешно создана!",
        parse_mode="HTML"
    )

#редактирование данных товара
@admin_router.callback_query(F.data.startswith("admin_edit_data"))
async def edit_data_product(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split(":")[-1])
    await state.update_data(item_id=item_id)

    await state.set_state(EditProductState.waiting_for_data)

    await callback.message.answer(f"💬 Введите новые данные товара: ")


@admin_router.message(EditProductState.waiting_for_data)
async def edit_data_product_fsm(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text.strip() if message.text.strip() else ""

    if not text:
        return await message.answer(f"❌ Данные товара должны быть строкой")

    new_data = text
    data_fsm = await state.get_data()
    item_id = data_fsm.get("item_id")

    if not item_id:
        await state.clear()
        return await message.answer(
            "⚠️ Ошибка: ID товара утерян. Попробуйте снова."
        )
    
    item = await session.get(Items, item_id)
    if not item:
        await state.clear()
        return await message.answer("❌ Товар не найден в базе данных.")

    item.data = new_data

    await session.commit()
    await state.clear()

    await message.answer(
        f"✅ Данные товара <b>#{item.id}</b> успешно обновлены на: {new_data}",
        parse_mode="HTML",
    )


#редактирование цены товара
@admin_router.callback_query(F.data.startswith("admin_edit_price"))
async def edit_price_product(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split(":")[-1])
    await state.update_data(item_id=item_id)

    await state.set_state(EditProductState.waiting_for_price)

    await callback.message.answer(f"💬 Введите новую стоимость товара: ")

@admin_router.message(EditProductState.waiting_for_price)
async def edit_price_product_fsm(message: Message, state: FSMContext, session: AsyncSession):
    text = (message.text or "").strip()

    # 1. Проверяем валидность целого числа и длину
    if not text.isdigit() or len(text) > 6:
        return await message.answer(
            "❌ Стоимость товара должна быть целым положительным числом (например: <code>150</code>)",
            parse_mode="HTML",
        )

    clean_price = Decimal(text)
    if clean_price <= 0:
        return await message.answer("❌ Стоимость товара должна быть больше 0.")

    data_fsm = await state.get_data()
    item_id = data_fsm.get("item_id")

    if not item_id:
        await state.clear()
        return await message.answer(
            "⚠️ Ошибка: ID товара утерян. Попробуйте снова."
        )

    item = await session.get(Items, item_id)
    if not item:
        await state.clear()
        return await message.answer("❌ Товар не найден в базе данных.")

    item.price = clean_price

    await session.commit()
    await state.clear()

    await message.answer(
        f"✅ Стоимость товара <b>#{item.id}</b> успешно обновлена на: <b>{clean_price:.2f} ₽</b>!",
        parse_mode="HTML",
    )

#рассылка пользователям
class UserMailingState(StatesGroup):
    waiting_for_message = State()

@admin_router.message(F.text == "👤 Рассылка")
async def user_mailing(message: Message, state: FSMContext):
    await state.set_state(UserMailingState.waiting_for_message)
    await message.answer(f"📢 Введите текст для рассылки всем пользователям бота: ",reply_markup=cancel_mailing_kb())

@admin_router.message(UserMailingState.waiting_for_message)
async def user_mailing_state(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    message_for_mailing = message.text
    await state.clear()

    ids_all_users = (await session.scalars(select(User.tg_id))).all()

    if not ids_all_users:
        return await message.answer("⚠️ В базе нет ни одного пользователя.")

    status_msg = await message.answer(f"⏳ Начинаю рассылку... Всего получателей: <code>{len(ids_all_users)}</code>",parse_mode="HTML")

    send_success = 0
    user_blocked = 0
    
    for chat_id in ids_all_users:
        if chat_id == settings.ADMIN_ID:
            continue
        try:
            await bot.send_message(chat_id=chat_id,text=message_for_mailing,parse_mode="HTML")
            send_success += 1

            await asyncio.sleep(0.05)

        except TelegramForbiddenError:
            user_blocked += 1
            continue

        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)

            await bot.send_message(chat_id=chat_id,text=message_for_mailing,parse_mode="HTML")
            send_success += 1

        except Exception:
            user_blocked += 1
            continue

    await status_msg.edit_text(
    "📊 <b>Рассылка завершена!</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    f"✅ Успешно доставлено: <code>{send_success}</code>\n"
    f"🚫 Не доставлено (блок бота): <code>{user_blocked}</code>\n"
    f"👥 Всего в базе: <code>{len(ids_all_users)}</code>\n"
    "━━━━━━━━━━━━━━━━━━━━━",
    parse_mode="HTML",
    )

#отмена рассылки пользователям
@admin_router.callback_query(F.data == "cancel_mailing")
async def cancel_mailing(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена.")

#создание промокодов


#async функция по генерации промокодов и проверка существования в базе
async def generation_promo_code(session: AsyncSession, length: int = 8):
    exclude = "0O1I"

    all_symbol = string.ascii_uppercase + string.digits
    clear_symbol = ''.join(s for s in all_symbol if s not in exclude)

    while True:
        promo_code = ''.join(secrets.choice(clear_symbol) for i in range(length))
        existing = await check_promocode(session, promo_code)

        if existing is None:
            return promo_code



#handler обработки нажатия кнопки и открытие FSM состояния
@admin_router.message(F.text == "🎫 Создать промокод")
async def create_promocode(message: Message, state: FSMContext):
    await state.set_state(PromoCodeState.waiting_for_code)

    await message.answer("🎫 Введите или сгенерируйте промокод: ", reply_markup=generation_code_kb())

#handler обработки нажатия "сгенерировать"
@admin_router.callback_query(PromoCodeState.waiting_for_code, F.data == "gen_code")
async def generation_code(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    
    promo_code = await generation_promo_code(session=session)
    await state.update_data(code=promo_code)

    await state.set_state(PromoCodeState.waiting_for_max_uses)
    await callback.message.answer(f"✨ Ваш сгенерированный промокод: <code>{promo_code}</code>\n\nТеперь введите кол-во использований: ",parse_mode='HTML')

#самостоятельный ввод промокода

@admin_router.message(PromoCodeState.waiting_for_code)
async def waiting_for_promocode(message: Message, state: FSMContext, session: AsyncSession):

    if not message.text:
        await message.answer("⚠️ Пожалуйста, отправьте промокод текстом (8 символов):")

    promo_code = message.text.strip().upper()

    if len(promo_code) > 8 or len(promo_code) < 8:
        return await message.answer("⚠️ Промокод должен содержать 8 символов. Попробуйте еще раз:")

    existing = await check_promocode(session, promo_code)

    if existing:
        await message.answer(
            f"❌ Промокод <code>{promo_code}</code> уже существует или использовался ранее.\n"
            "Введите другой промокод:",
            parse_mode="HTML"
        )
        return

    await state.update_data(code=promo_code)
    await state.set_state(PromoCodeState.waiting_for_max_uses)

    await message.answer(
        f"✅ Промокод <code>{promo_code}</code> принят!\n\n"
        "Теперь укажите <b>максимальное количество использований</b> (целое число):",
        parse_mode="HTML"
    )

#обработа FSM состояния кол-ва использований

@admin_router.message(PromoCodeState.waiting_for_max_uses)
async def max_uses(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""

    # Проверяем, что это строго положительное целое число
    if not text.isdigit() or int(text) <= 0:
        return await message.answer(
            "⚠️ Пожалуйста, введите положительное целое число (больше 0):"
        )

    uses_count = int(text)

    # Защита от неадекватно больших значений
    if uses_count > 100_000:
        return await message.answer(
            "⚠️ Слишком большое число. Введите значение до 100 000:"
        )

    await state.update_data(max_uses=uses_count)
    await state.set_state(PromoCodeState.waiting_for_amount)

    await message.answer(
        f"✅ Лимит использований: <b>{uses_count}</b>\n\n"
        f"Теперь укажите <b>сумму награды</b> (целое число):",
        parse_mode="HTML",
    )


# обработа FSM состояния суммы вознаграждения
@admin_router.message(PromoCodeState.waiting_for_amount)
async def amount_promocode(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text.strip() if message.text else ""

    # Проверяем, что это строго положительное целое число
    if not text.isdigit() or int(text) <= 0:
        return await message.answer(
            "⚠️ Пожалуйста, введите положительное целое число (больше 0):"
        )

    amount = int(text)
    

    data = await state.get_data()

    code = data.get("code")
    max_uses = data.get("max_uses")

    # Страховка на случай сброса состояния
    if not code or not max_uses:
        await state.clear()
        return await message.answer("⚠️ Данные устарели. Начните создание промокода заново.")

    create_promo = PromoCode(
        code=data.get("code"),
        max_uses=data.get("max_uses"),
        reward_amount=amount
    )

    session.add(create_promo)
    await session.commit()
    await state.clear()

    await message.answer(
        f"🎉 <b>Промокод успешно создан!</b>\n\n"
        f"Код: <code>{code}</code>\n"
        f"Активаций: <b>{max_uses}</b>\n"
        f"Награда: <b>{amount}</b>",
        parse_mode="HTML"
    )