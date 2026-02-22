import aiohttp
from config import settings

BASE_URL = f"https://proxy6.net/api/{settings.PROXY6_API_KEY}/"

async def _request(method: str, params: dict = None):
    if params is None:
        params = {}
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL + method, params=params) as resp:
            data = await resp.json()
            if data.get("status") == "yes":
                return data
            return None

async def get_countries(version: int = 4):
    res = await _request("getcountry", {"version": version})
    if res and "list" in res:
        return res["list"]
    return []

async def get_price(count: int, period: int, version: int = 4):
    res = await _request("getprice", {"count": count, "period": period, "version": version})
    if res:
        return res.get("price"), res.get("price_single")
    return None, None

async def buy_proxy(count: int, period: int, country: str, version: int = 4, type_: str = "http"):
    params = {
        "count": count,
        "period": period,
        "country": country,
        "version": version,
        "type": type_
    }
    return await _request("buy", params)

async def get_proxies(state="active"):
    return await _request("getproxy", {"state": state})
