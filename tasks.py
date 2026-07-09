from aiogram import Bot
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards import task_keyboard, review_keyboard
from database import (
    get_tasks,
    complete_task,
    create_submission,
    approve_submission,
    reject_submission
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

    task_id = int(
        callback.data.split("_")[1]
    )


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

    task_id = int(
        callback.data.split("_")[1]
    )


    await state.update_data(
        task_id=task_id
    )


    await state.set_state(
        TaskState.waiting_for_proof
    )


    await callback.message.answer(
        "📷 أرسل الآن صورة إثبات إتمام المهمة."
    )


    await callback.answer()




@router.message(
    TaskState.waiting_for_proof,
    F.photo
)
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


    submission_id = create_submission(
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

        ),

        reply_markup=review_keyboard(
            submission_id
        )

    )


    await message.answer(
        "✅ تم استلام صورة الإثبات.\n"
        "سيتم مراجعتها من قبل الإدارة."
    )


    await state.clear()



# قبول الإثبات
@router.callback_query(
    F.data.startswith("approve_")
)
async def approve_button(
    callback: CallbackQuery,
    bot: Bot
):

    submission_id = int(
        callback.data.split("_")[1]
    )


    submission = approve_submission(
        submission_id
    )


    if not submission:
        await callback.answer(
            "تمت معالجة الطلب مسبقًا."
        )
        return


    await bot.send_message(
        submission["telegram_id"],
        "✅ تم قبول إثباتك!\n"
        f"⭐ حصلت على {submission['points']} نقطة."
    )


    await callback.message.edit_caption(
        callback.message.caption +
        "\n\n✅ تم القبول"
    )


    await callback.answer(
        "تم قبول الطلب"
    )



# رفض الإثبات
@router.callback_query(
    F.data.startswith("reject_")
)
async def reject_button(
    callback: CallbackQuery,
    bot: Bot
):

    submission_id = int(
        callback.data.split("_")[1]
    )


    submission = reject_submission(
        submission_id
    )


    if not submission:
        await callback.answer(
            "تمت معالجة الطلب مسبقًا."
        )
        return


    await bot.send_message(
        submission["telegram_id"],
        "❌ تم رفض إثباتك.\n"
        "يمكنك المحاولة مرة أخرى."
    )


    await callback.message.edit_caption(
        callback.message.caption +
        "\n\n❌ تم الرفض"
    )


    await callback.answer(
        "تم رفض الطلب"
    )
