from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards import main_keyboard
from database import (
    get_user,
    add_user,
    get_points,
    get_leaderboard,
    get_referrals,
    add_referral_reward,
    set_referred_by,
    get_referred_by
)
from config import TOKEN
from tasks import router as tasks_router

import asyncio
import os
from aiohttp import web


bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(tasks_router)


@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    user = get_user(user_id)

    if not user:
        add_user(
            user_id,
            username,
            first_name
        )

    await message.answer(
        "💰 مرحبًا بك في Kasib\n\n"
        "اكسب النقاط، شارك في المسابقات، واربح الجوائز!\n\n"
        "اختر أحد الخيارات من القائمة 👇",
        reply_markup=main_keyboard
    )


@dp.message(F.text == "⭐ نقاطي")
async def my_points(message: Message):
    points = get_points(message.from_user.id)

    await message.answer(
        f"⭐ نقاطك الحالية: {points}"
    )


@dp.message(F.text == "🎟️ بطاقات السحب")
async def tickets(message: Message):
    await message.answer(
        "🎟️ لا تملك أي بطاقة سحب حتى الآن."
    )


@dp.message(F.text == "🎁 المسابقات")
async def contests(message: Message):
    await message.answer(
        "🎁 لا توجد مسابقات نشطة حاليًا."
    )


@dp.message(F.text == "🏆 المتصدرون")
async def leaderboard(message: Message):

    users = get_leaderboard()

    if not users:
        await message.answer(
            "🏆 لا يوجد متصدرون حتى الآن."
        )
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    text = "🏆 أفضل 5 متصدرين\n\n"

    for i, user in enumerate(users):
        name = user["first_name"] or "مستخدم"
        points = user["points"]

        text += (
            f"{medals[i]} {name} — "
            f"{points} نقطة\n"
        )

    text += (
        "\n⭐ اجمع المزيد من النقاط "
        "لتصل إلى المراكز الخمسة الأولى!"
    )

    await message.answer(text)


@dp.message(F.text == "👥 دعوة صديق")
async def invite(message: Message):

    referrals = get_referrals(
        message.from_user.id
    )

    bot_username = (await bot.get_me()).username

    link = (
        f"https://t.me/{bot_username}"
        f"?start={message.from_user.id}"
    )

    await message.answer(

        "👥 دعوة الأصدقاء\n\n"

        f"🔗 رابط دعوتك:\n{link}\n\n"

        f"👤 عدد الدعوات: {referrals}\n\n"

        "🎁 تحصل على 10 نقاط "
        "عن كل مستخدم جديد يدخل عبر رابطك."

    )


@dp.message(F.text == "📜 القوانين")
async def rules(message: Message):
    await message.answer(
        "📜 قوانين Kasib ستضاف هنا."
    )


@dp.message(F.text == "📞 الدعم")
async def support(message: Message):
    await message.answer(
        "📞 تواصل مع الدعم قريبًا."
    )


async def health(request):
    return web.Response(
        text="Kasib Bot is running!"
    )


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
