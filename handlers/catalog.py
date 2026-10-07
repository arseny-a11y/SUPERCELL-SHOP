import math
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Categories, Items, SubCategories
from database.queries import ProductsQueries
from aiogram.exceptions import TelegramBadRequest
from config.config import settings
from handlers.admin import ADMIN_IDS
from keyboards.inline import (
    CategoryCD,
    ItemsCD,
    ItemsPageCD,
    SubCategoryCD,
    keyboard_categories,
    item_card_keyboard,
    sub_categories_kb,
    items_pagination_keyboards,
)


catalog_router = Router()

@catalog_router.message(F.text == "Каталог товаров 🛒")
async def open_catalog(message: Message, session: AsyncSession):

    categories = await ProductsQueries.get_all_categories(session)
    if not categories:
        return await message.answer("Каталог пока пуст. Скоро здесь появятся товары!")
    
    await message.answer("Выберите интересующий раздел:",reply_markup=keyboard_categories(categories))

@catalog_router.callback_query(CategoryCD.filter())
async def show_category_pagination(callback: CallbackQuery,callback_data: CategoryCD, session: AsyncSession):
    is_admin = (
        callback.from_user.id in ADMIN_IDS
    )
    category_id = callback_data.category_id

    sub_cat = (await session.scalars(select(SubCategories).where(SubCategories.category_id == callback_data.category_id))).all()
    
    if not sub_cat and not is_admin:
        return await callback.answer("⚠️ В этом разделе пока нет товара.", show_alert=True)
        
    await callback.message.edit_text("Выберите подкатегорию:", reply_markup=sub_categories_kb(category_id, sub_cat, is_admin))
    await callback.answer()

@catalog_router.callback_query(SubCategoryCD.filter())
async def sub_categories(callback: CallbackQuery, callback_data: SubCategoryCD, session: AsyncSession):
    is_admin = (
        callback.from_user.id in ADMIN_IDS
    )
    # ID конкретной выбранной подкатегории
    sub_category_id = callback_data.sub_category_id

    page = 1
    ITEMS_PER_PAGE = 5
    
    sub_category = await session.get(SubCategories, sub_category_id)
    
    if not sub_category:
        return await callback.answer("⚠️ Подкатегория не найдена", show_alert=True)
    
    is_product = (await session.scalars(select(Items.id).where(Items.category_id == sub_category_id).where(Items.is_sold.is_(False)))).all()

    if not is_product and not is_admin:
            return await callback.answer("⚠️ В этой подкатегории пока нет товаров в наличии",show_alert=True)
    
    offset, total_page, items = await ProductsQueries.get_items(
        session, page, ITEMS_PER_PAGE, sub_category_id
    )

    text = f"📦 <b>Товары {sub_category.name}</b>\n\n"
    await callback.message.edit_text(
        text=text,
        reply_markup=items_pagination_keyboards(
            page=page,
            total_page=total_page,
            category_id=sub_category_id,
            items=items,
            is_admin=is_admin
        ),
        parse_mode='HTML'
    )
    await callback.answer()

@catalog_router.callback_query(ItemsPageCD.filter())
async def pagination_button(callback: CallbackQuery, callback_data: ItemsPageCD, session: AsyncSession):

    is_admin = (
        callback.from_user.id in ADMIN_IDS
    )

    sub_category_id = callback_data.category_id
    page = callback_data.page
    ITEMS_PER_PAGE = 5

    sub_category = await session.get(SubCategories, sub_category_id)
    if not sub_category:
        return await callback.answer("⚠️ Подкатегория не найдена", show_alert=True)

    offset, total_page, items = await ProductsQueries.get_items(
        session, page, ITEMS_PER_PAGE, sub_category_id
    )

    text = f"📦 <b>Товары {sub_category.name}</b>\n\n"

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=items_pagination_keyboards(
                page=page,
                total_page=total_page,
                category_id=sub_category_id,
                items=items,
                is_admin=is_admin
            ),
            parse_mode='HTML'
        )

    except TelegramBadRequest as e:
        if "message is not modified" not in e.message:
            raise e

    await callback.answer()


@catalog_router.callback_query(ItemsCD.filter())
async def back_to_product(callback: CallbackQuery, callback_data: ItemsCD, session: AsyncSession):
    is_admin = (
        callback.from_user.id in ADMIN_IDS
    )
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
        await callback.message.edit_text(text,reply_markup=item_card_keyboard(item_id,item.category_id, is_admin=is_admin),parse_mode='HTML')

    except TelegramBadRequest as e:
        if "message is not modified" not in e.message:
            raise e
        
    await callback.answer()


@catalog_router.callback_query(F.data == "back_to_categories")
async def back_to_categories_menu(callback: CallbackQuery, session: AsyncSession):
    is_admin = callback.from_user.id in ADMIN_IDS
    categories = await ProductsQueries.get_all_categories(session)
    if not categories:
        return await callback.answer("Каталог пока пуст. Скоро здесь появятся товары!")
    
    await callback.message.edit_text(text="Выберите интересующий раздел:",reply_markup=keyboard_categories(categories, is_admin))
    await callback.answer()

