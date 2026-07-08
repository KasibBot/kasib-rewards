from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import task_keyboard
from database import get_tasks, complete_task

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
async def send_proof(callback: CallbackQuery):
    await callback.message.answer(
        "📷 أرسل الآن صورة إثبات إتمام المهمة.\n\n"
        "بعد إرسالها سيتم تحويلها إلى الإدارة للمراجعة."
    )

    await callback.answer()
