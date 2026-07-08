from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
import asyncio
import os
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎉 أهلاً بك في Kasib!\n\n"
        "💰 شاهد الفيديوهات، اجمع النقاط، واربح الجوائز."
    )


# صفحة صغيرة حتى يقبل Render الخدمة كـ Web Service
async def health(request):
    return web.Response(text="Kasib Bot is running!")


async def run_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        "0.0.0.0",
        int(os.getenv("PORT", 10000))
    )
    await site.start()


async def main():
    await run_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
