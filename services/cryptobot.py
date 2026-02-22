import aiohttp
from config import settings

BASE_URL = "https://pay.crypt.bot/api/"

async def create_invoice(amount: float):
    headers = {"Crypto-Pay-API-Token": settings.CRYPTOBOT_API_TOKEN}
    payload = {
        "asset": "USDT",
        "currency_type": "fiat",
        "fiat": "RUB",
        "amount": str(amount),
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(BASE_URL + "createInvoice", json=payload) as resp:
            data = await resp.json()
            if data.get("ok"):
                return data["result"]
            return None

async def get_invoice(invoice_id: int):
    headers = {"Crypto-Pay-API-Token": settings.CRYPTOBOT_API_TOKEN}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(BASE_URL + "getInvoices", params={"invoice_ids": invoice_id}) as resp:
            data = await resp.json()
            if data.get("ok") and data["result"]["items"]:
                return data["result"]["items"][0]
            return None
