from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from database import async_session
from models import User, ProxyOrder
from services.proxy6 import get_countries, get_price, buy_proxy
from keyboards import buy_types_kb, buy_countries_kb, periods_kb, confirm_buy_kb
from datetime import datetime

router = Router()

@router.message(F.text == "📲 Купить")
async def buy_start(message: Message):
    await message.answer("Выберите тип прокси:", reply_markup=buy_types_kb())

@router.callback_query(F.data.startswith("buy_type_"))
async def choose_country(callback: CallbackQuery):
    version = int(callback.data.split("_")[2])
    countries = await get_countries(version)
    if not countries:
        await callback.answer("Нет доступных стран для этого типа.", show_alert=True)
        return
    await callback.message.edit_text("Выберите страну:", reply_markup=buy_countries_kb(countries, version))

@router.callback_query(F.data.startswith("buy_country_"))
async def choose_period(callback: CallbackQuery):
    _, _, version, country = callback.data.split("_")
    await callback.message.edit_text(f"Тип: IPv{version}, Страна: {country.upper()}\nВыберите период:", reply_markup=periods_kb(version, country))

@router.callback_query(F.data.startswith("buy_period_"))
async def choose_count(callback: CallbackQuery):
    _, _, version, country, period = callback.data.split("_")
    count = 1
    
    price_total, _ = await get_price(count, int(period), int(version))
    if price_total is None:
        await callback.message.edit_text("Ошибка получения цены от провайдера.")
        return
        
    text = f"Резюме заказа:\nТип: IPv{version}\nСтрана: {country.upper()}\nПериод: {period} дней\nКоличество: {count} шт\n\nИтого: {price_total} RUB"
    await callback.message.edit_text(text, reply_markup=confirm_buy_kb(version, country, period, count))

@router.callback_query(F.data.startswith("confirm_buy_"))
async def confirm_buy(callback: CallbackQuery):
    _, _, version, country, period, count = callback.data.split("_")
    count = int(count)
    period = int(period)
    version = int(version)
    
    price_total, _ = await get_price(count, period, version)
    if not price_total:
        await callback.answer("Ошибка получения цены.", show_alert=True)
        return

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
        if user.balance < price_total:
            await callback.answer("Недостаточно средств на балансе!", show_alert=True)
            return
            
        res = await buy_proxy(count, period, country, version=version)
        if not res or res.get("status") != "yes":
            await callback.message.edit_text("Ошибка при покупке прокси на стороне провайдера. Попробуйте другую страну или позже.")
            return
        
        user.balance -= price_total
        
        proxies = res.get("list", {})
        for pid, pdata in proxies.items():
            date_end = None
            if "date_end" in pdata:
                try:
                    date_end = datetime.strptime(pdata["date_end"], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
                    
            order = ProxyOrder(
                user_id=user.id,
                proxy_id=str(pid),
                ip=pdata.get("ip", ""),
                port_http=pdata.get("port", ""),
                port_socks5=pdata.get("port", ""),
                username=pdata.get("user", ""),
                password=pdata.get("pass", ""),
                date_end=date_end,
                country=country
            )
            session.add(order)
            
            await callback.message.answer(
                f"✅ Успешная покупка!\n\nIP: {order.ip}\nHTTP Порт: {order.port_http}\n"
                f"SOCKS5 Порт: {order.port_socks5}\nЛогин: {order.username}\nПароль: {order.password}\n"
                f"Действует до: {order.date_end.strftime('%d.%m.%Y %H:%M') if order.date_end else 'неизвестно'}"
            )

        await session.commit()
    await callback.message.delete()

@router.callback_query(F.data == "cancel_buy")
async def cancel_buy(callback: CallbackQuery):
    await callback.message.edit_text("Покупка отменена.")
