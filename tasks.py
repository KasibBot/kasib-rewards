from aiogram import Bot
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards import task_keyboard
from database import (
    get_tasks,
    complete_task,
    create_submission
)
from config import GROUP_ID
from states import TaskState

router = Router()


@router.message(F.text == "📋 المهام")
async def tasks(message: Message):
    tasks_list = get_tasks()

    if not tasks_list:
        await message.answer(
            "📋 لا توجد مهام متاحة حاليًا."
        )
        return

    for task in tasks_list:
        await message.answer(
            f"🔹 {task['title']}\n"
            f"⭐ المكافأة: {task['points']} نقطة",
            reply_markup=task_keyboard(
                task["id"],
                task["url"]
            )
        )


@router.callback_query(F.data.startswith("complete_"))
async def complete_task_button(callback: CallbackQuery):
    user_id = callback.from_user.id
    task_id = int(callback.data.split("_")[1])

    tasks_list = get_tasks()

    task = next(
        (t for t in tasks_list if t["id"] == task_id),
        None
    )

    if not task:
        await callback.answer(
            "المهمة غير موجودة"
        )
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


@router.callback_query(F.data.startswith("proof_"))
async def send_proof(
    callback: CallbackQuery,
    state: FSMContext
):
    task_id = int(callback.data.split("_")[1])

    await state.update_data(task_id=task_id)

    await state.set_state(
        TaskState.waiting_for_proof
    )

    await callback.message.answer(
        "📷 أرسل الآن صورة إثبات إتمام المهمة."
    )

    await callback.answer()

@router.message(TaskState.waiting_for_proof, F.photo)
async def receive_proof(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    data = await state.get_data()
    task_id = data["task_id"]

    tasks_list = get_tasks()

    task = next(
        (t for t in tasks_list if t["id"] == task_id),
        None
    )

    if not task:
        await message.answer(
            "❌ المهمة غير موجودة."
        )
        await state.clear()
        return

    photo_id = message.photo[-1].file_id

    create_submission(
        message.from_user.id,
        task_id,
        photo_id,
        task["points"]
    )

    await bot.send_photo(
        chat_id=GROUP_ID,
        photo=photo_id,
        caption=(
            "📥 إثبات جديد\n\n"
            f"👤 المستخدم: {message.from_user.full_name}\n"
            f"🆔 Telegram ID: {message.from_user.id}\n"
            f"📋 المهمة: {task['title']}\n"
            f"⭐ النقاط: {task['points']}"
        )
    )

    await message.answer(
        "✅ تم استلام صورة الإثبات.\n"
        "سيتم مراجعتها من قبل الإدارة."
    )

    await state.clear()
