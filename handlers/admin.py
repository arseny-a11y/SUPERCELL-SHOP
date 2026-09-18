from aiogram.filters import BaseFilter, Command
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.config import settings
from keyboards.reply import admin_menu 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Categories, Items
from keyboards.inline import category_admin,create_category
from database.queries import CreatedCategories
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

class AdminUploadItems(StatesGroup):
    waiting_for_category = State()
    waiting_for_file = State()

class CreateCategory(StatesGroup):
    waiting_for_name = State() 

@admin_router.message(F.text == "📥 Загрузить (.txt) файл товаров")
async def upload_items(message: Message, session: AsyncSession, state: FSMContext):
    categories = (await session.scalars(select(Categories))).all()

    if not categories:
        return await message.answer("Создайте хоть одну категорию!",reply_markup=create_category())

    
    await state.set_state(AdminUploadItems.waiting_for_category)
    await message.answer("Выберите категорию, в которую будут загружены товары:", reply_markup=category_admin(categories))

@admin_router.callback_query(AdminUploadItems.waiting_for_category, F.data.startswith("admin_cat_"))
async def category_selected(callback: CallbackQuery, state: FSMContext,):
    cat_id = int(callback.data.split("_")[-1])
    await state.update_data(cat_id=cat_id)

    await state.set_state(AdminUploadItems.waiting_for_file)

    await callback.message.edit_text(
        "Категория выбрана.\n\n"
        "Отправьте <b>.txt</b> файл со списком товаров документом.\n"
        "Формат строки:\n"
        "<code>Название | Описание | Цена | Данные_товара</code>",
        parse_mode="HTML"
    )  

    await callback.answer()

@admin_router.message(AdminUploadItems.waiting_for_file, F.document)
async def upload_items(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if not message.document.file_name.endswith(".txt"):
        return await message.answer("❌ Отправьте файл с расширением (.txt)")

    category_id = await state.get_data()
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

        if len(data_account) != 4:
            return await message.answer(f"❌ Ошибка: в строке {num}: ожидалось 4 поля через '|'")
        
        title, desc, price, data = data_account

        try:
            check_price = int(price)
        except ValueError:
            return await message.answer(f"❌ Ошибка: Цена не является цислом в строке {num}")

        products.append(
            Items(
                 category_id=category_id["cat_id"],
                 title=title,
                 description=desc,
                 price=int(price),
                 data=data,
                 is_sold=False
            )
        )
    session.add_all(products)
    await session.commit() 

    await state.clear()   
    await message.answer(f"✅ Успешно добавлено товаров: <b>{len(products)}</b> шт.", parse_mode="HTML")


@admin_router.callback_query(F.data == "create_category")
async def created_category_button(callback: CallbackQuery,state: FSMContext):
    await state.set_state(CreateCategory.waiting_for_name)
    await callback.message.edit_text("💬 Введите название категории: ")
    await callback.answer()
@admin_router.message(CreateCategory.waiting_for_name)
async def created_category_fsm(message: Message, state: FSMContext, session: AsyncSession):
    category_name = message.text.strip()
    if not category_name:
        return await message.answer("❌ Название категории не может быть пустым")
    
    await CreatedCategories.new_category(session, category_name)

    await message.answer(f"✅ Категория «{category_name}» создана!")
    await state.clear()


@admin_router.callback_query(F.data == "admin_cancel_upload")
async def cancel_upload(callback: CallbackQuery, state: FSMContext):
   await state.clear()
   await callback.message.edit_text("Загрузка отменена ❌")
   await callback.answer()