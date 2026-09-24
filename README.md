<div align="center">

# 🛒 SUP SHOP — Telegram Bot для продажи цифровых товаров

Асинхронный Telegram-бот с удобной витриной товаров, админ-панелью и автоматическим приемом платежей в криптовалюте через **Crypto Pay (CryptoBot)**.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://github.com/aiogram/aiogram)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![HTTPX](https://img.shields.io/badge/HTTPX-Async-1f425f?style=for-the-badge)](https://www.python-httpx.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

---

## 🚀 Основной функционал

* **Интерактивный каталог:** удобная навигация по категориям и карточкам товаров на inline-кнопках.
* **Автоматическая оплата:** создание инвойсов через Crypto Pay API с автоконвертацией рублей в эквивалент USDT по актуальному биржевому курсу.
* **Моментальная выдача:** отправка данных купленного товара (аккаунты, ключи, ссылки) сразу после подтверждения транзакции.
* **Защита от race conditions:** атомарное обновление статуса товара в базе данных (`UPDATE ... WHERE is_sold = False RETURNING ...`) исключает двойную выдачу одной позиции при параллельных кликах.
* **Безопасная архитектура:** строгая валидация колбэков через Pydantic (без передачи цен и чувствительных данных на сторону клиента).

---

## 🛠 Стек технологий

* **Язык:** Python 3.11+
* **Фреймворк:** [aiogram 3.x](https://github.com/aiogram/aiogram) (роутеры, фильтры, FSM, типизированные CallbackData)
* **База данных:** SQLite / PostgreSQL
* **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (AsyncEngine, Declarative Base)
* **HTTP-клиент:** [httpx](https://www.python-httpx.org/) (асинхронные запросы к Crypto Pay API с обработкой таймаутов)
* **Конфигурация:** [pydantic-settings](https://docs.pydantic.dev/latest/) (.env окружение)

---

## 📂 Структура проекта

```text
├── handlers/            # Обработчики сообщений и колбэков (каталог, оплата, админка)
├── keyboards/           # Сборка inline и reply клавиатур
├── middlewares/         # Middleware (сессии БД, обработка ошибок)
├── database/            # Модели SQLAlchemy и фабрика асинхронных сессий
├── payments/            # Интеграция со сторонними API (клиент CryptoPay)
├── crypto_pay.py        # Код оплаты CryptoBot
├── config.py            # Валидация переменных окружения через Pydantic
├── main.py              # Инициализация и точка входа (polling)
└── requirements.txt     # Зависимости проекта
