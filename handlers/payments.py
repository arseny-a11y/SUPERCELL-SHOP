from config.config import settings
from payments.crypto_pay import CryptoPay
from keyboards.inline import BuyCD, PayCheckCD
from keyboards.inline import check_pay_keyboard
from database.models import Items
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from aiogram import Router, F
from aiogram.types import CallbackQuery

router_pay = Router()
crypto = CryptoPay(settings.CRYPTO_PAY_TOKEN)

@router_pay.callback_query(BuyCD.filter())
async def payment_product(callback: CallbackQuery,callback_data: BuyCD, session: AsyncSession):
    item = await session.get(Items,callback_data.item_id)

    if not item:
        return await callback.answer("Товар не найден или удален", show_alert=True)
    
    if item.is_sold:
        return await callback.answer("Товар куплен другим пользователем",show_alert=True)

    
    invoice = await crypto.create_invoice(
        amount=item.price,
        )
    if not invoice:
        return await callback.answer("Ошибка связи с платежкой, попробуйте позже.", show_alert=True)

    await callback.message.answer(f"Счет #{invoice['invoice_id']} сформирован.\nПосле оплаты нажмите кнопку проверки:",reply_markup=check_pay_keyboard(invoice,callback_data.item_id))

@router_pay.callback_query(PayCheckCD.filter())
async def check_payment(callback: CallbackQuery, callback_data: PayCheckCD,session: AsyncSession):
    invoice = await crypto.get_invoice(callback_data.invoice_id)

    if not invoice:
        return await callback.answer("Не удалось найти счет. Попробуйте еще раз.",show_alert=True)

    status = invoice.get("status")

    if status == "active":
        return await callback.answer("Оплата пока не поступила. Подождите пару секунд и проверьте снова.", show_alert=True)

    if status != "paid":
        return await callback.answer(f"Счет не действителен (статус: {status}).", show_alert=True)

    stmt = (
        update(Items).
        where(Items.id == callback_data.item_id, Items.is_sold.is_(False))
        .values(is_sold = True)
        .returning(Items.data)
    )

    result = await session.execute(stmt)

    item_data = result.scalar_one_or_none()

    await session.commit()

    if item_data is None:
        return await callback.answer("Этот товар уже был выдан!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        f"Оплата подтверждена!\n\n"
        f"Ваш товар:\n`{item_data}`",
        parse_mode="Markdown",
    )
    await callback.answer()