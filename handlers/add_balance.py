from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import async_session
from models import User, Invoice
from services.cryptobot import create_invoice, get_invoice
from sqlalchemy import select
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

class BalanceState(StatesGroup):
    waiting_for_amount = State()

@router.callback_query(F.data == "add_balance")
async def add_balance_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите сумму для пополнения в RUB (минимум 10):")
    await state.set_state(BalanceState.waiting_for_amount)

@router.message(BalanceState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount < 10:
            await message.answer("Минимальная сумма пополнения 10 RUB.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")
        return
        
    inv = await create_invoice(amount)
    if not inv:
        await message.answer("Ошибка создания счета. Проверьте настройки API или попробуйте позже.")
        await state.clear()
        return
        
    invoice_id = inv.get("invoice_id")
    pay_url = inv.get("bot_invoice_url") or inv.get("pay_url")
    
    if not invoice_id or not pay_url:
        await message.answer("Ошибка в ответе API CryptoBot.")
        await state.clear()
        return
        
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        db_inv = Invoice(user_id=user.id, invoice_id=invoice_id, amount=amount)
        session.add(db_inv)
        await session.commit()
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить", url=pay_url)],
        [InlineKeyboardButton(text="Проверить оплату", callback_data=f"check_invoice_{invoice_id}")]
    ])
    
    await message.answer("Счет создан! Оплатите его по кнопке ниже, затем нажмите 'Проверить оплату'.", reply_markup=kb)
    await state.clear()

@router.callback_query(F.data.startswith("check_invoice_"))
async def check_invoice(callback: CallbackQuery):
    invoice_id = int(callback.data.split("_")[2])
    
    inv_data = await get_invoice(invoice_id)
    if not inv_data:
        await callback.answer("Счет не найден или API недоступно.")
        return
        
    if inv_data.get("status") == "paid":
        async with async_session() as session:
            db_inv = await session.scalar(select(Invoice).where(Invoice.invoice_id == invoice_id))
            if db_inv and db_inv.status != "paid":
                db_inv.status = "paid"
                user = await session.get(User, db_inv.user_id)
                user.balance += db_inv.amount
                await session.commit()
                await callback.message.edit_text(f"✅ Оплата прошла успешно! Ваш баланс пополнен на {db_inv.amount} RUB.")
            elif db_inv and db_inv.status == "paid":
                await callback.answer("Счет уже обработан.")
            else:
                await callback.answer("Счет не найден в локальной БД.")
    else:
        await callback.answer("Счет еще не оплачен!", show_alert=True)
