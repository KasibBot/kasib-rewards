from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards import main_keyboard, task_keyboard
from database import get_user, add_user, get_points, get_tasks, complete_task
import asyncio
import os
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


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


@dp.message(F.text == "📋 المهام")
async def tasks(message: Message):
    tasks_list = get_tasks()

    if not tasks_list:
        await message.answer("📋 لا توجد مهام متاحة حاليًا.")
        return

    for task in tasks_list:
        await message.answer(
            f"🔹 {task['title']}\n"
            f"⭐ المكافأة: {task['points']} نقطة\n"
            f"🔗 الرابط: {task['url']}",
            reply_markup=task_keyboard(task["id"])
        )


@dp.callback_query(F.data.startswith("complete_"))
async def complete_task_button(callback: CallbackQuery):
    user_id = callback.from_user.id

    task_id = int(callback.data.split("_")[1])

    tasks_list = get_tasks()

    task = next(
        (t for t in tasks_list if t["id"] == task_id),
        None
    )

    if not task:
        await callback.answer("المهمة غير موجودة")
        return

    result = complete_task(
        user_id,
        task_id,
        task["points"]
    )

    if result:
        await callback.message.answer(
            f"🎉 تم إكمال المهمة!\n"
            f"⭐ حصلت على {task['points']} نقطة."
        )
    else:
        await callback.message.answer(
            "⚠️ لقد أكملت هذه المهمة من قبل."
        )

    await callback.answer()


@dp.message(F.text == "🎟️ بطاقات السحب")
async def tickets(message: Message):
    await message.answer("🎟️ لا تملك أي بطاقة سحب حتى الآن.")


@dp.message(F.text == "🎁 المسابقات")
async def contests(message: Message):
    await message.answer("🎁 لا توجد مسابقات نشطة حاليًا.")


@dp.message(F.text == "🏆 المتصدرون")
async def leaderboard(message: Message):
    await message.answer("🏆 سيتم عرض المتصدرين هنا.")


@dp.message(F.text == "👥 دعوة صديق")
async def invite(message: Message):
    await message.answer("👥 رابط الدعوة الخاص بك سيظهر هنا.")


@dp.message(F.text == "📜 القوانين")
async def rules(message: Message):
    await message.answer("📜 قوانين Kasib ستضاف هنا.")


@dp.message(F.text == "📞 الدعم")
async def support(message: Message):
    await message.answer("📞 تواصل مع الدعم قريبًا.")


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
