import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from config import settings
from database import init_db
from handlers import common, buy, add_balance

logging.basicConfig(level=logging.INFO)

async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    logging.info("Dummy web server started on port 5000")

async def main():
    await init_db()
    
    # Start web server to satisfy Replit's port 5000 check
    await start_web_server()
    
    if not settings.TELEGRAM_BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN is not set. Please set it in secrets/environment variables.")
        # Keep running the loop so the web server stays alive
        while True:
            await asyncio.sleep(3600)
        
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(common.router)
    dp.include_router(buy.router)
    dp.include_router(add_balance.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
