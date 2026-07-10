from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from keyboards import main_keyboard
from database import (
    get_user,
    add_user,
    get_points,
    get_leaderboard,
    get_referrals,
    add_referral_reward,
    set_referred_by,
    get_referred_by,
    get_users_count,
    add_points
)
from config import TOKEN
from tasks import router as tasks_router
from database import supabase
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from states import AdminTaskState

import asyncio
import os
from aiohttp import web
from aiogram.fsm.state import State, StatesGroup

ADMIN_ID = 1924476173
SUPPORT_CHAT_ID = -1004469291192

class AdminTaskState(StatesGroup):
    waiting_for_title = State()
    waiting_for_url = State()
    waiting_for_points = State()

class SupportState(StatesGroup):
    waiting_for_message = State()
    
class ContestState(StatesGroup):
    waiting_for_title = State()
    waiting_for_prize = State()
    waiting_for_winners = State()    
    
bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(tasks_router)
admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ إضافة مهمة",
                callback_data="add_task"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 عرض المهام",
                callback_data="show_tasks"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏆 إنشاء مسابقة",
                callback_data="create_contest"
            )
        ],
        [
    InlineKeyboardButton(
        text="🎲 إجراء السحب",
        callback_data="run_draw"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ حذف مهمة",
                callback_data="delete_task"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 عدد المستخدمين",
                callback_data="admin_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 الإحصائيات",
                callback_data="admin_stats"
            )
        ]
    ]
)

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    args = message.text.split()

    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
        except ValueError:
            referrer_id = None

    user = get_user(user_id)

    if not user:
        add_user(
            user_id,
            username or "",
            first_name or "",
            referrer_id
        )

        if referrer_id and referrer_id != user_id:
            add_points(referrer_id, 10)

    await message.answer(
        "💰 مرحبًا بك في Kasib\n\n"
        "اكسب النقاط، شارك في المسابقات، واربح الجوائز!\n\n"
        "اختر أحد الخيارات من القائمة 👇",
        reply_markup=main_keyboard
    )

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙️ لوحة تحكم الأدمن",
        reply_markup=admin_keyboard
    )
@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback):
    if callback.from_user.id != ADMIN_ID:
        return

    count = get_users_count()

    await callback.message.answer(
        f"👥 عدد المستخدمين: {count}"
    )


@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback):
    if callback.from_user.id != ADMIN_ID:
        return

    count = get_users_count()

    await callback.message.answer(
        f"📊 الإحصائيات:\n\n"
        f"👥 عدد المستخدمين: {count}\n"
        f"🤝 نظام الإحالة: مفعل\n"
        f"💰 مكافأة الإحالة: 10 نقاط"
    )
@dp.callback_query(lambda c: c.data == "show_tasks")
async def show_tasks(callback):
    if callback.from_user.id != ADMIN_ID:
        return

    tasks = supabase.table("tasks").select("*").execute()

    if not tasks.data:
        await callback.message.answer("📋 لا توجد مهام حاليا")
        return

    text = "📋 قائمة المهام:\n\n"

    for task in tasks.data:
        text += (
            f"🆔 ID: {task['id']}\n"
            f"📌 العنوان: {task['title']}\n"
            f"🔗 الرابط: {task['url']}\n"
            f"💰 النقاط: {task['points']}\n"
            f"✅ نشطة: {task['active']}\n\n"
        )

    await callback.message.answer(text)


@dp.callback_query(lambda c: c.data == "add_task")
async def add_task_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.message.answer("📌 أرسل عنوان المهمة:")
    await state.set_state(AdminTaskState.waiting_for_title)


@dp.message(AdminTaskState.waiting_for_title)
async def get_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)

    await message.answer("🔗 أرسل رابط المهمة:")
    await state.set_state(AdminTaskState.waiting_for_url)

@dp.message(AdminTaskState.waiting_for_url)
async def get_task_url(message: Message, state: FSMContext):
    
    await state.update_data(url=message.text)
    await message.answer("💰 أرسل عدد نقاط المهمة:")
    await state.set_state(AdminTaskState.waiting_for_points)
@dp.message(AdminTaskState.waiting_for_points)
async def get_task_points(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ أرسل رقمًا صحيحًا فقط.")
        return

    data = await state.get_data()

    supabase.table("tasks").insert({
        "title": data["title"],
        "url": data["url"],
        "points": int(message.text),
        "active": True
    }).execute()

    await message.answer("✅ تم إضافة المهمة بنجاح.")
    await state.clear()


@dp.callback_query(lambda c: c.data == "create_contest")
async def create_contest_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.message.answer("🏆 أرسل اسم المسابقة:")
    await state.set_state(ContestState.waiting_for_title)


@dp.message(ContestState.waiting_for_title)
async def get_contest_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)

    await message.answer("🎁 أرسل الجائزة:")
    await state.set_state(ContestState.waiting_for_prize)


@dp.message(ContestState.waiting_for_prize)
async def get_contest_prize(message: Message, state: FSMContext):
    await state.update_data(prize=message.text)

    await message.answer("👥 أرسل عدد الفائزين:")
    await state.set_state(ContestState.waiting_for_winners)


@dp.message(ContestState.waiting_for_winners)
async def get_contest_winners(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ أرسل رقمًا صحيحًا.")
        return

    data = await state.get_data()

    supabase.table("contests").insert({
        "title": data["title"],
        "prize": data["prize"],
        "winners_count": int(message.text),
        "status": "active"
    }).execute()

    await message.answer("✅ تم إنشاء المسابقة بنجاح.")
    await state.clear()


@dp.callback_query(lambda c: c.data == "delete_task")
async def delete_task_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tasks = supabase.table("tasks").select("*").eq("active", True).execute()

    if not tasks.data:
        await callback.message.answer("❌ لا توجد مهام.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for task in tasks.data:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=task["title"],
                callback_data=f"del_{task['id']}"
            )
        ])

    await callback.message.answer(
        "🗑 اختر المهمة التي تريد حذفها:",
        reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data.startswith("del_"))
async def delete_task(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    task_id = int(callback.data.replace("del_", ""))

    supabase.table("tasks").delete().eq("id", task_id).execute()

    await callback.message.edit_text("✅ تم حذف المهمة بنجاح.")
exchange_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ تأكيد",
                callback_data="confirm_exchange"
            ),
            InlineKeyboardButton(
                text="❌ إلغاء",
                callback_data="cancel_exchange"
            )
        ]
    ]
)
@dp.callback_query(lambda c: c.data == "run_draw")
async def run_draw(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    contest = supabase.table("contests") \
        .select("*") \
        .eq("status", "active") \
        .limit(1) \
        .execute()

    if not contest.data:
        await callback.message.answer("❌ لا توجد مسابقة نشطة.")
        return

    c = contest.data[0]

    users = supabase.table("users") \
        .select("telegram_id, username, tickets") \
        .gt("tickets", 0) \
        .execute()

    if not users.data:
        await callback.message.answer("❌ لا يوجد مشاركون.")
        return

    import random

    pool = []

    for user in users.data:
        for _ in range(user["tickets"]):
            pool.append({
                "telegram_id": user["telegram_id"],
                "username": user["username"]
            })

    winners_count = c["winners_count"]

    if len(pool) < winners_count:
        winners_count = len(pool)

    winners = []

    while len(winners) < winners_count and pool:
        winner = random.choice(pool)

        if winner not in winners:
            winners.append(winner)

        pool = [x for x in pool if x != winner]

    text = "🎉 الفائزون:\n\n"

    for i, winner in enumerate(winners, start=1):
        name = f"@{winner['username']}" if winner["username"] else str(winner["telegram_id"])

        text += f"{i}- {name}\n"

        await bot.send_message(
            winner["telegram_id"],
            "🎉 مبروك! لقد فزت في المسابقة!"
        )

    await callback.message.answer(text)

    supabase.table("contests").update({
        "status": "finished"
    }).eq("id", c["id"]).execute()


supabase.table("users") \
    .update({"tickets": 0}) \
    .gt("tickets", 0) \
    .execute()
    
@dp.message(F.text == "⭐ نقاطي")
async def my_points(message: Message):
    points = get_points(message.from_user.id)

    await message.answer(
        f"⭐ نقاطك الحالية: {points}"
    )


@dp.message(F.text == "🎟️ بطاقات السحب")
async def tickets(message: Message):
    user = supabase.table("users") \
        .select("tickets") \
        .eq("telegram_id", message.from_user.id) \
        .execute()

    if not user.data:
        await message.answer("❌ لم يتم العثور على حسابك.")
        return

    tickets = user.data[0]["tickets"]

    if tickets <= 0:
        await message.answer("🎟️ لا تملك أي بطاقة سحب حتى الآن.")
        return

    await message.answer(
        f"🎟️ لديك {tickets} بطاقة سحب."
    )
@dp.message(F.text == "🎟️ استبدال النقاط")
async def exchange_points(message: Message):
    user = supabase.table("users") \
        .select("points") \
        .eq("telegram_id", message.from_user.id) \
        .execute()

    if not user.data:
        await message.answer("❌ لم يتم العثور على حسابك.")
        return

    points = user.data[0]["points"]

    if points < 1000:
        await message.answer(
            f"❌ لا تملك نقاط كافية.\n"
            f"رصيدك: {points} نقطة\n"
            f"المطلوب: 1000 نقطة 🎟️"
        )
        return

    await message.answer(
        "🎟️ هل تريد استبدال 1000 نقطة؟",
        reply_markup=exchange_keyboard
    )
@dp.callback_query(lambda c: c.data == "confirm_exchange")
async def confirm_exchange(callback: CallbackQuery):
    try:
        user = supabase.table("users") \
            .select("points, tickets") \
            .eq("telegram_id", callback.from_user.id) \
            .execute()

        if not user.data:
            await callback.answer("❌ الحساب غير موجود")
            return

        points = user.data[0]["points"]
        tickets = user.data[0]["tickets"]

        if points < 1000:
            await callback.answer("❌ نقاطك غير كافية")
            return

        supabase.table("users").update({
            "points": points - 1000,
            "tickets": tickets + 1
        }).eq("telegram_id", callback.from_user.id).execute()

        await callback.message.edit_text(
            "✅ تم الاستبدال بنجاح!\n🎟️ حصلت على بطاقة سحب."
        )

    except Exception as e:
        await callback.message.answer(f"❌ خطأ: {e}")
    
@dp.message(F.text == "🎁 المسابقات")
async def contests(message: Message):
    contest = supabase.table("contests") \
        .select("*") \
        .eq("status", "active") \
        .limit(1) \
        .execute()

    if not contest.data:
        await message.answer("🎁 لا توجد مسابقات نشطة حاليًا.")
        return

    user = supabase.table("users") \
        .select("tickets") \
        .eq("telegram_id", message.from_user.id) \
        .execute()

    tickets = 0
    if user.data:
        tickets = user.data[0]["tickets"]

    c = contest.data[0]

    await message.answer(
        f"🏆 {c['title']}\n\n"
        f"🎁 الجائزة: {c['prize']}\n"
        f"👥 عدد الفائزين: {c['winners_count']}\n\n"
        f"🎟️ بطاقاتك: {tickets}"
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
        "📜 قوانين Kasib\n\n"
        "🎯 طريقة المشاركة:\n"
        "• شاهد مقاطع الفيديو حتى النهاية.\n"
        "• بعد إكمال المشاهدة ستحصل على النقاط حسب المهمة.\n"
        "• استبدل نقاطك ببطاقات سحب للمشاركة في المسابقات.\n\n"
        "📋 القوانين:\n"
        "1️⃣ يجب مشاهدة الفيديو حتى النهاية حتى تُحتسب المهمة.\n"
        "2️⃣ يمنع استخدام أي وسيلة غش أو التحايل للحصول على النقاط.\n"
        "3️⃣ كل بطاقة سحب تمنح فرصة واحدة للفوز.\n"
        "4️⃣ كلما زاد عدد بطاقاتك زادت فرصك في السحب.\n"
        "5️⃣ يتم اختيار الفائز عشوائيًا بواسطة البوت.\n"
        "6️⃣ يحق للإدارة استبعاد أي حساب مخالف أو إلغاء مشاركته."
    )


@dp.message(F.text == "📞 الدعم")
async def support(message: Message, state: FSMContext):
    await message.answer(
        "📩 أرسل رسالتك الآن، وسيتم إرسالها إلى فريق الدعم."
    )
    await state.set_state(SupportState.waiting_for_message)
@dp.message(SupportState.waiting_for_message)
async def receive_support_message(message: Message, state: FSMContext):
    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "لا يوجد"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📩 رد",
                    callback_data=f"reply_{message.from_user.id}"
                )
            ]
        ]
    )

    await bot.send_message(
        SUPPORT_CHAT_ID,
        f"📩 طلب دعم جديد\n\n"
        f"👤 الاسم: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"🔗 المعرف: {username}\n\n"
        f"💬 الرسالة:\n{message.text}",
        reply_markup=keyboard
    )

    await message.answer(
        "✅ تم إرسال رسالتك إلى فريق الدعم، وسيتم الرد عليك في أقرب وقت."
    )

    await state.clear()


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
    print("1- Starting web server")
    await run_web_server()

    while True:
        try:
            print("2- Deleting webhook")
            await bot.delete_webhook(drop_pending_updates=True)

            print("3- Starting polling")
            await dp.start_polling(bot)

        except Exception as e:
            print(f"Polling stopped بسبب خطأ: {e}")
            print("إعادة التشغيل بعد 5 ثوان...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
