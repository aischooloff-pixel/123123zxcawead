from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from database import async_session
from models import User, ProxyOrder
from keyboards import main_menu, profile_kb, info_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if not user:
            user = User(telegram_id=message.from_user.id, username=message.from_user.username)
            session.add(user)
            await session.commit()
            await session.refresh(user)

    await message.answer(
        f"Добро пожаловать!\nВаш баланс: {user.balance} RUB\n\nИспользуйте меню для навигации.", 
        reply_markup=main_menu()
    )

@router.message(F.text == "🖥 Профиль")
async def profile_handler(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if not user:
            return
        
        proxies = (await session.scalars(select(ProxyOrder).where(ProxyOrder.user_id == user.id))).all()
            
    text = f"👤 Ваш ID: {user.telegram_id}\n💰 Баланс: {user.balance} RUB\n\n📁 Список активных прокси:"
    await message.answer(text, reply_markup=profile_kb(proxies))

@router.callback_query(F.data.startswith("view_proxy_"))
async def view_proxy_details(callback: CallbackQuery):
    proxy_id = int(callback.data.split("_")[2])
    async with async_session() as session:
        proxy = await session.get(ProxyOrder, proxy_id)
        if not proxy:
            await callback.answer("Прокси не найдена.", show_alert=True)
            return
            
    text = (
        f"🌐 Прокси: {proxy.ip}\n"
        f"🔑 Данные:\n"
        f"Хост: {proxy.ip}\n"
        f"Порт HTTP: {proxy.port_http}\n"
        f"Порт SOCKS5: {proxy.port_socks5}\n"
        f"Логин: {proxy.username}\n"
        f"Пароль: {proxy.password}\n"
        f"📅 Срок до: {proxy.date_end.strftime('%d.%m.%Y %H:%M') if proxy.date_end else 'Бессрочно'}"
    )
    await callback.message.answer(text)
    await callback.answer()

@router.message(F.text == "ℹ️ Информация")
async def info_handler(message: Message):
    text = "ℹ️ Информация о сервисе\n\nМы предоставляем качественные прокси по доступным ценам."
    await message.answer(text, reply_markup=info_kb())

@router.callback_query(F.data == "view_rules")
async def view_rules(callback: CallbackQuery):
    rules = (
        "📖 Правила нашего сервиса:\n\n"
        "1. Запрещено сосать прокси для незаконной деятельности.\n"
        "2. Возврат средств не предусмотрен после активации прокси.\n"
        "3. Мы не несем ответственности за блокировки в сторонних сервисах.\n"
        "4. Техническая поддержка работает с 10:00 до 22:00 по МСК."
    )
    await callback.message.answer(rules)
    await callback.answer()
