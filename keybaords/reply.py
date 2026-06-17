from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def reply_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="📅 Забронировать столик"),
        KeyboardButton(text="🗂 Мои бронирования"),
        KeyboardButton(text="🍽️ Предзаказ еды"),
        KeyboardButton(text="❓ Помощь"),
        KeyboardButton(text="ℹ️ О боте"),
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)
