from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def create_keyboard_menu() -> ReplyKeyboardMarkup:

    kb = [
        [KeyboardButton(text='Каталог товаров 🛒')],
        [KeyboardButton(text='Профиль 👤'), KeyboardButton(text='Пополнить баланс 📥')],
        [KeyboardButton(text='ℹ️ О SUP SHOP'), KeyboardButton(text='🆘 Поддержка')]
        ]
    keyboard_menu = ReplyKeyboardMarkup(keyboard=kb,resize_keyboard=True)

    return keyboard_menu