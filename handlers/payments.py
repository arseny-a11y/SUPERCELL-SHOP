from config.config import settings
from payments.crypto_pay import CryptoPay
from keyboards.inline import BuyCD, top_up_balance_crypto_kb
from database.models import Items, Payments, User, Orders
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from decimal import Decimal

router_pay = Router()
crypto = CryptoPay(settings.CRYPTO_PAY_TOKEN)


"""Код выдачи товара сразу после оплаты, без пополнение баланса (Прошлый вариант)"""
# @router_pay.callback_query(BuyCD.filter())
# async def payment_product(callback: CallbackQuery,callback_data: BuyCD, session: AsyncSession):
#     item = await session.get(Items,callback_data.item_id)

#     if not item:
#         return await callback.answer("Товар не найден или удален", show_alert=True)
    
#     if item.is_sold:
#         return await callback.answer("Товар куплен другим пользователем",show_alert=True)

    
#     invoice = await crypto.create_invoice(
#         amount=item.price,
#         )
#     if not invoice:
#         return await callback.answer("Ошибка связи с платежкой, попробуйте позже.", show_alert=True)

#     await callback.message.answer(f"Счет #{invoice['invoice_id']} сформирован.\nПосле оплаты нажмите кнопку проверки:",reply_markup=check_pay_keyboard(invoice,callback_data.item_id))

# @router_pay.callback_query(PayCheckCD.filter())
# async def check_payment(callback: CallbackQuery, callback_data: PayCheckCD,session: AsyncSession):
#     invoice = await crypto.get_invoice(callback_data.invoice_id)

#     if not invoice:
#         return await callback.answer("Не удалось найти счет. Попробуйте еще раз.",show_alert=True)

#     status = invoice.get("status")

#     if status == "active":
#         return await callback.answer("Оплата пока не поступила. Подождите пару секунд и проверьте снова.", show_alert=True)

#     if status != "paid":
#         return await callback.answer(f"Счет не действителен (статус: {status}).", show_alert=True)

#     stmt = (
#         update(Items).
#         where(Items.id == callback_data.item_id, Items.is_sold.is_(False))
#         .values(is_sold = True)
#         .returning(Items.data)
#     )

#     result = await session.execute(stmt)

#     item_data = result.scalar_one_or_none()

#     await session.commit()

#     if item_data is None:
#         return await callback.answer("Этот товар уже был выдан!", show_alert=True)
#     await callback.message.edit_reply_markup(reply_markup=None)

#     await callback.message.answer(
#         f"Оплата подтверждена!\n\n"
#         f"Ваш товар:\n`{item_data}`",
#         parse_mode="Markdown",
#     )
#     await callback.answer()

# Пополнение баланса

class TopUpBalance(StatesGroup):
    waiting_for_amount = State()



@router_pay.message(F.text == "Пополнить баланс 📥")
async def top_up_balance(message: Message, state: FSMContext):
    await state.set_state(TopUpBalance.waiting_for_amount)

    await message.answer("Введите сумму пополнения в рублях (минимум 50 ₽):")

@router_pay.callback_query(F.data == "top_up_balance")
async def top_up_balance(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TopUpBalance.waiting_for_amount)

    await callback.message.answer("Введите сумму пополнения в рублях (минимум 50 ₽):")

@router_pay.message(TopUpBalance.waiting_for_amount)
async def process_top_up(message: Message, state: FSMContext):
    amount = message.text

    if not amount.isdigit():
        return await message.answer("❌ Пожалуйста, введите целое положительное число")

    if int(amount) < 50:
        return await message.answer("❌ Минимальная сумма поплнения - 50 ₽")
    await state.clear()

    invoice = await crypto.create_invoice(
        amount=amount
    )

    await message.answer(f"Счёт на сумму **{amount} ₽** сформирован. После оплаты нажмите «Проверить оплату».",reply_markup=top_up_balance_crypto_kb(amount,invoice))

@router_pay.callback_query(F.data.startswith("check_pay_crypto"))
async def check_payment(callback: CallbackQuery,session: AsyncSession):
    invoice_id = int(callback.data.split(":")[-1])
    invoice = await crypto.get_invoice(invoice_id)

    if not invoice:
        return await callback.answer("Не удалось найти счет. Попробуйте еще раз.",show_alert=True)

    invoice_status = invoice.get("status")

    if invoice_status == "active":
        return await callback.answer("Оплата пока не поступила. Подождите пару секунд и проверьте снова.", show_alert=True)
    
    if invoice_status != "paid":
        return await callback.answer(f"Счет не действителен (статус: {invoice_status}).", show_alert=True)

    check_stmt = (select(Payments).where(Payments.invoice_id == invoice_id, Payments.status == "paid"))
    execute_check_stmt = (await session.execute(check_stmt)).scalar_one_or_none()

    if execute_check_stmt:
        return await callback.answer("Этот счет уже был успешно зачислен!", show_alert=True)

    amount = Decimal(str(invoice.get("amount",0)))


    new_payment = Payments(
        user_id=callback.from_user.id,
        invoice_id=invoice_id,
        amount=invoice.get("amount"),
        payment_system="CryptoBot",
        status=invoice_status,
    )
    session.add(new_payment)

    top_up_balance_user = (
        update(User).
        where(User.tg_id == callback.from_user.id).
        values(balance=User.balance + amount).
        returning(User.balance)
    )
    result = await session.execute(top_up_balance_user)
    new_balance = result.scalar_one_or_none()

    await session.commit()


    session.add(new_payment)
    await session.commit()

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ Оплата прошла успешно!\n\n"
        f"Пополнено: **{amount} ₽**\n"
        f"Ваш текущий баланс: **{new_balance} ₽**",
        parse_mode="Markdown",
    )
    await callback.answer()


#Оплата конкретного товара

@router_pay.callback_query(BuyCD.filter())
async def buy_product(
    callback: CallbackQuery, callback_data: BuyCD, session: AsyncSession
):
    item_id = callback_data.item_id

    
    user = await session.scalar(
        select(User).where(User.tg_id == callback.from_user.id)
    )
    if not user:
        return await callback.answer(
            "Пользователь не найден.", show_alert=True
        )

    item = await session.scalar(
        select(Items).where(Items.id == item_id, Items.is_sold.is_(False))
    )
    if not item:
        return await callback.answer(
            "Товар не найден или уже продан!", show_alert=True
        )

    if user.balance < item.price:
        diff = item.price - user.balance
        return await callback.answer(
            f"Недостаточно средств! Не хватает {diff:.2f} ₽.",
            show_alert=True,
        )

    user.balance -= item.price
    item.is_sold = True

    # 5. Создаем заказ
    new_order = Orders(
        user_id=user.tg_id,
        item_id=item.id,
        price=item.price,
        item_data=item.data,
    )
    session.add(new_order)

    await session.commit()


    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ **Покупка успешно совершена!**\n\n"
        f"Списано: `{item.price} ₽`\n"
        f"Остаток: `{user.balance} ₽`\n\n"
        f"📦 **Данные товара:**\n`{item.data}`",
        parse_mode="Markdown",
    )
    await callback.answer()