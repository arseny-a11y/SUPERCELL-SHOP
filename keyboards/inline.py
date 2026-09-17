from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
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

# Меню со списком категорий
def keyboard_categories(categories: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for cat in categories:
        kb.button(text=cat.name,callback_data=CategoryCD(category_id=cat.id))
    kb.adjust(1)
    return kb.as_markup()

#меню со списком товаров + кнопка "назад"

def keyboard_items(items: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for item in items:
        kb.button(text=f"{item.title} | {item.price}",callback_data=ItemsCD(item_id=item.id))
    kb.button(text="◀️ Назад к категориям",callback_data="back_to_categories")
    kb.adjust(1)
    return kb.as_markup()

def item_card_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="💳 Купить", callback_data=BuyCD(item_id=product_id))
    kb.button(text="◀️ Назад к списку",callback_data=CategoryCD(category_id=category_id))

    kb.adjust(1)
    return kb.as_markup()