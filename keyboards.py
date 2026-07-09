from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⭐ نقاطي"),
            KeyboardButton(text="📋 المهام")
        ],
        [
            KeyboardButton(text="🎟️ استبدال النقاط"),
            KeyboardButton(text="🎟️ بطاقات السحب")
        ],
        [
            KeyboardButton(text="🎁 المسابقات"),
            KeyboardButton(text="👥 دعوة صديق")
        ],
        [
            KeyboardButton(text="🏆 المتصدرون"),
            KeyboardButton(text="📜 القوانين")
        ],
        [
            KeyboardButton(text="📞 الدعم")
        ]
    ],
    resize_keyboard=True
)


def task_keyboard(task_id, url):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 فتح المهمة",
                    url=url
                )
            ],
            [
                InlineKeyboardButton(
                    text="📤 إرسال الإثبات",
                    callback_data=f"proof_{task_id}"
                )
            ]
        ]
    )
def review_keyboard(submission_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ قبول",
                    callback_data=f"approve_{submission_id}"
                ),
                InlineKeyboardButton(
                    text="❌ رفض",
                    callback_data=f"reject_{submission_id}"
                )
            ]
        ]
    )
