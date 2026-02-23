from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    kb = [
        [KeyboardButton(text="📲 Сосать"), KeyboardButton(text="🖥 Профиль")],
        [KeyboardButton(text="ℹ️ Информация")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def profile_kb(proxies=None):
    builder = InlineKeyboardBuilder()
    if proxies:
        for p in proxies:
            builder.button(text=f"proxy {p.ip}", callback_data=f"view_proxy_{p.id}")
    builder.button(text="💳 Пополнить баланс", callback_data="add_balance")
    builder.adjust(1)
    return builder.as_markup()

def info_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Админ", url="https://t.me/your_admin_username")],
        [InlineKeyboardButton(text="🔗 Канал", url="https://t.me/your_channel_username")],
        [InlineKeyboardButton(text="📖 Правила", callback_data="view_rules")]
    ])

def buy_types_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="IPv4", callback_data="buy_type_4")],
        [InlineKeyboardButton(text="IPv6", callback_data="buy_type_6")],
        [InlineKeyboardButton(text="IPv4 Shared", callback_data="buy_type_3")]
    ])

def buy_countries_kb(countries, version):
    builder = InlineKeyboardBuilder()
    for c in countries:
        builder.button(text=c.upper(), callback_data=f"buy_country_{version}_{c}")
    builder.adjust(3)
    return builder.as_markup()

def periods_kb(version: str, country: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="3 дня", callback_data=f"buy_period_{version}_{country}_3")],
        [InlineKeyboardButton(text="7 дней", callback_data=f"buy_period_{version}_{country}_7")],
        [InlineKeyboardButton(text="30 дней", callback_data=f"buy_period_{version}_{country}_30")]
    ])

def confirm_buy_kb(version: str, country: str, period: int, count: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_buy_{version}_{country}_{period}_{count}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_buy")]
    ])
