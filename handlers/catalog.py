import math
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Categories, Items
from database.queries import ProductsQueries
from aiogram.exceptions import TelegramBadRequest
from keyboards.inline import (
    CategoryCD,
    ItemsCD,
    ItemsPageCD,
    keyboard_categories,
    item_card_keyboard,
    items_pagination_keyboards,
)


catalog_router = Router()

@catalog_router.message(F.text == "Каталог товаров 🛒")
async def open_catalog(message: Message, session: AsyncSession):
    categories = await ProductsQueries.get_all_categories(session)
    if not categories:
        return await message.answer("Каталог пока пуст. Скоро здесь появятся товары!")
    await message.answer("Выберите интересующий раздел:",reply_markup=keyboard_categories(categories))

# @catalog_router.callback_query(CategoryCD.filter())
# async def show_category_items(callback: CallbackQuery,callback_data: CategoryCD,session: AsyncSession):
#     items = await ProductsQueries.get_product(session, callback_data)

#     if not items:
#         await callback.answer("В этой категории нет доступных товаров.",show_alert=True)
#         return

#     await callback.message.edit_text(
#         "Выберите товар из списка:",
#         reply_markup=keyboard_items(items)
#     )
#     await callback.answer()

@catalog_router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, session: AsyncSession):
    categories = await ProductsQueries.get_all_categories(session)
    if not categories:
        return await callback.answer("Каталог пока пуст. Скоро здесь появятся товары!")
    
    await callback.message.edit_text(text="Выберите интересующий раздел:",reply_markup=keyboard_categories(categories))
    await callback.answer()

@catalog_router.callback_query(ItemsCD.filter())
async def back_to_product(callback: CallbackQuery, callback_data: ItemsCD, session: AsyncSession):
    item_id = callback_data.item_id
    item = await session.scalar(select(Items).where(Items.id == item_id, Items.is_sold.is_(False)))

    if not item:
        return await callback.answer("Товар купили!",show_alert=True)
    text = (
         f"<b>{item.title}</b>\n\n"
         f"{item.description}\n\n"
         f"🪙Цена: {item.price}"
    )
    try:
        await callback.message.edit_text(text,reply_markup=item_card_keyboard(item_id,item.category_id),parse_mode='HTML')

    except TelegramBadRequest as e:
        if "message is not modified" not in e.message:
            raise e
        
    await callback.answer()

#обработчик пагинаций

@catalog_router.callback_query(CategoryCD.filter())
async def show_category_pagination(callback: CallbackQuery,callback_data: CategoryCD, session: AsyncSession):
    category_id = callback_data.category_id
    page = 1

    ITEMS_PER_PAGE = 5

    offset, total_page, items = await ProductsQueries.get_items(session,page,ITEMS_PER_PAGE,category_id)

    category = (await session.scalars(select(Categories).where(Categories.id == category_id))).one_or_none()

    if not category:
        text = "⚠️ Категория не найдена"
    else:
        text = f"📦 <b>Товары {category.name}</b>\n\n"

    await callback.message.edit_text(
        text=text,
        reply_markup=items_pagination_keyboards(
            page=page,
            total_page=total_page,
            category_id=category_id,
            items=items,
        ),
        parse_mode='HTML'
    )
    await callback.answer()


@catalog_router.callback_query(ItemsPageCD.filter())
async def pagination_button(callback: CallbackQuery, callback_data: ItemsPageCD,session: AsyncSession):
    category_id = callback_data.category_id
    page = callback_data.page

    ITEMS_PER_PAGE = 5

    offset, total_page, items = await ProductsQueries.get_items(session,page,ITEMS_PER_PAGE,category_id)

    category = (await session.scalars(select(Categories).where(Categories.id == category_id))).one_or_none()

    if not category:
        text = "⚠️ Категория не найдена"
    else:
        text = f"📦 <b>Товары {category.name}</b>\n\n"

    await callback.message.edit_text(
        text=text,
        reply_markup=items_pagination_keyboards(
            page=page,
            total_page=total_page,
            category_id=category_id,
            items=items,
        ),
        parse_mode='HTML'
    )
    await callback.answer()