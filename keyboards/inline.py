from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

def keyboard_support() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text='👤 Поддержка',url='https://t.me/gemaglobin')

    return kb.as_markup()

def keyboard_profile() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text='📂 История покупок',callback_data='purchases')
    kb.button(text='Пополнить баланс 📥',callback_data='up_balance')


    return kb.as_markup()


#функционал каталога
class CategoryCD(CallbackData,prefix='cat'):
    category_id: int

class ItemsCD(CallbackData,prefix='prod'):
    item_id: int

class BuyCD(CallbackData,prefix='buy'):
    item_id: int

class ItemsPageCD(CallbackData,prefix='items_page'):
    category_id: int
    page: int

class PayCheckCD(CallbackData,prefix='chek_pay'):
    invoice_id: int
    item_id: int



# Меню со списком категорий
def keyboard_categories(categories: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for cat in categories:
        kb.button(text=cat.name,callback_data=CategoryCD(category_id=cat.id).pack())
    kb.adjust(1)
    return kb.as_markup()

#меню со списком товаров + кнопка "назад"

# def keyboard_items(items: list) -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()

#     for item in items:
#         kb.button(text=f"{item.title} | {item.price}",callback_data=ItemsCD(item_id=item.id).pack())
#     kb.button(text="◀️ Назад к категориям",callback_data="back_to_categories")
#     kb.adjust(1)
#     return kb.as_markup()

def item_card_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="💳 Купить", callback_data=BuyCD(item_id=product_id).pack())
    kb.button(text="◀️ Назад к списку",callback_data=CategoryCD(category_id=category_id).pack())

    kb.adjust(1)
    return kb.as_markup()


#категории товаров для админа
def category_admin(categories: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for cat in categories:
        kb.button(text=cat.name, callback_data=f"admin_cat_{cat.id}")
    kb.button(text="❌ Отмена", callback_data="admin_cancel_upload")
    kb.button(text="📦 Создать категорию",callback_data="create_category")

    kb.adjust(2)
    return kb.as_markup()

def create_category() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="📦 Создать категорию",callback_data="create_category")
    return kb.as_markup()

# пролистывание меню по стрелочкам <>

def items_pagination_keyboards(page: int, total_page: int, category_id: int, items: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for item in items:
        kb.row(
            InlineKeyboardButton(
                text=f"💎 {item.title} | {item.price}₽",callback_data=ItemsCD(item_id=item.id).pack()
            )
        )
    pagination = []

    if page > 1:
        pagination.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=ItemsPageCD(
                    category_id=category_id,
                    page=page - 1
                ).pack()
            )
        )

    pagination.append(
        InlineKeyboardButton(
            text=f"{page}/{total_page}",
            callback_data="ignore"
        )
    )

    if page < total_page:
        pagination.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=ItemsPageCD(
                    category_id=category_id,
                    page=page + 1
                ).pack()
            )
        )


    kb.row(*pagination)

    kb.row(
        InlineKeyboardButton(
            text="◀️ Назад к категориям",
            callback_data="back_to_categories"
        )
    )

    return kb.as_markup()

#Создание клавиатуры для проверки оплаты

def check_pay_keyboard(invoice: dict,item_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="Оплатить",url=invoice["bot_invoice_url"])
    kb.button(text="Проверить оплату",callback_data=PayCheckCD(invoice_id=invoice["invoice_id"],item_id=item_id))

    kb.adjust(1)

    return kb.as_markup()