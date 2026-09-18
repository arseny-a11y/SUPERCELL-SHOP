from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def create_keyboard_menu() -> ReplyKeyboardMarkup:

    kb = [
        [KeyboardButton(text='Каталог товаров 🛒')],
        [KeyboardButton(text='Профиль 👤'), KeyboardButton(text='Пополнить баланс 📥')],
        [KeyboardButton(text='ℹ️ О SUP SHOP'), KeyboardButton(text='🆘 Поддержка')]
        ]
    keyboard_menu = ReplyKeyboardMarkup(keyboard=kb,resize_keyboard=True)

    return keyboard_menu

#меню администатора 
def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.add(
        KeyboardButton(text="📥 Загрузить (.txt) файл товаров"),
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="📦 Управление товарами")
    )

    kb.adjust(1,2)
    return kb.as_markup(resize_keyboard=True)