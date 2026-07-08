from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⭐ نقاطي"), KeyboardButton(text="🎟️ بطاقات السحب")],
        [KeyboardButton(text="📋 المهام"), KeyboardButton(text="🎁 المسابقات")],
        [KeyboardButton(text="🏆 المتصدرون"), KeyboardButton(text="👥 دعوة صديق")],
        [KeyboardButton(text="📜 القوانين"), KeyboardButton(text="📞 الدعم")],
    ],
    resize_keyboard=True
)
