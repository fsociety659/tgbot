import json
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from text import start_text
from keybaords.reply import reply_kb
from database.requests import (
    get_user_bookings,
    delete_booking,
    get_food_order_by_booking,
    get_booking_by_id,
)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(start_text, parse_mode="HTML", reply_markup=reply_kb())


@router.message(Command("mybookings"))
@router.message(F.text == "🗂 Мои бронирования")
async def cmd_mybookings(message: Message):
    user_id = message.from_user.id
    bookings = await get_user_bookings(user_id)

    if not bookings:
        await message.answer("📋 У вас пока нет броней.", reply_markup=reply_kb())
        return

    bookings_text = "📋 <b>Ваши бронирования:</b>\n\n"
    for booking in bookings:
        status = "✅ Оплачено" if booking["is_paid"] else "⏳ Ожидает оплаты"
        bookings_text += (
            f"<b>Бронь #{booking['id']}</b>\n"
            f"📅 Дата: {booking['booking_date']}\n"
            f"⏰ Время: {booking['booking_time']}\n"
            f"👥 Гостей: {booking['guests_count']} чел.\n"
            f"📍 Место: {booking['table_location']}\n"
            f"💰 Сумма: {booking['total_price']}₽\n"
            f"💳 Статус: {status}\n"
        )

        food = await get_food_order_by_booking(booking["id"])
        if food:
            food_status = (
                "✅ Оплачено онлайн" if food["is_paid"] else "💵 Оплата на месте"
            )
            try:
                items = json.loads(food["items"])
            except Exception:
                items = []
            bookings_text += "━━━━━━━━━━━━━━━━━━━━\n🍱 <b>ВАШ ПРЕДЗАКАЗ ЕДЫ:</b>\n"
            for name, count in items:
                bookings_text += f"• {name} ({count} шт)\n"
            bookings_text += f"💰 Статус еды: {food_status}\n━━━━━━━━━━━━━━━━━━━━\n"

        bookings_text += f"/del_{booking['id']} — отменить\n\n"

    await message.answer(bookings_text, reply_markup=reply_kb())


@router.message(F.text.regexp(r"^/del_\d+$"))
async def cmd_cancel_booking(message: Message):
    try:
        booking_id = int(message.text.split("_")[1])
        user_id = message.from_user.id

        booking = await get_booking_by_id(booking_id)
        if booking and booking["user_id"] == user_id:
            try:
                booking_dt = datetime.strptime(
                    f"{booking['booking_date']} {booking['booking_time']}",
                    "%d.%m.%Y %H:%M",
                )
                diff = (booking_dt - datetime.now()).total_seconds() / 3600
                if 0 < diff < 2:
                    await message.answer(
                        f"⚠️ <b>До вашей брони осталось менее 2 часов!</b>\n\n"
                        f"Отмена в это время платная — <b>200₽</b>.\n\n"
                        f"Для подтверждения платной отмены напишите:\n"
                        f"/delconfirm_{booking_id}",
                        reply_markup=reply_kb(),
                    )
                    return
            except ValueError:
                pass

        deleted = await delete_booking(booking_id, user_id)
        if deleted:
            await message.answer(
                f"✅ Бронь #{booking_id} успешно отменена.", reply_markup=reply_kb()
            )
        else:
            await message.answer(
                "❌ Бронь не найдена или уже была отменена ранее.",
                reply_markup=reply_kb(),
            )
    except (IndexError, ValueError):
        await message.answer(
            "❌ Неверный формат команды. Используйте /del_<ID>", reply_markup=reply_kb()
        )


@router.message(F.text.regexp(r"^/delconfirm_\d+$"))
async def cmd_confirm_paid_cancel(message: Message):
    try:
        booking_id = int(message.text.split("_")[1])
        user_id = message.from_user.id

        deleted = await delete_booking(booking_id, user_id)
        if deleted:
            await message.answer(
                f"✅ Бронь #{booking_id} отменена.\n"
                f"💳 С вас будет списано <b>200₽</b> за позднюю отмену.",
                reply_markup=reply_kb(),
            )
        else:
            await message.answer(
                "❌ Бронь не найдена или уже была отменена ранее.",
                reply_markup=reply_kb(),
            )
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды.", reply_markup=reply_kb())


@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "❓ <b>Помощь и правила бронирования</b>\n\n"
        "👋 <b>Краткое руководство по кнопкам:</b>\n"
        "• <b>Забронировать столик</b> — выбор даты, времени, локации и количества гостей.\n"
        "• <b>Мои бронирования</b> — просмотр активных броней и оформление отмены.\n"
        "• <b>Предзаказ еды</b> — добавление блюд из меню к вашей активной брони.\n\n"
        "⚠️ <b>Важно об отмене:</b>\n"
        "Отмена бронирования менее чем за 2 часа — платная (200₽ удерживаются из депозита).\n\n"
        "📞 <b>Контакты для связи:</b>\n"
        "Если у вас возникли вопросы по оплате или составу заказа, наш администратор всегда на связи:\n"
        "💬 <b>Telegram:</b> @eco1kd\n"
        "☎️ <b>Телефон:</b> +7 (960) 188-55-08",
        reply_markup=reply_kb(),
    )


@router.message(F.text == "ℹ️ О боте")
async def cmd_about(message: Message):
    await message.answer(
        "🏛 <b>О нашем ресторане</b>\n\n"
        "Добро пожаловать! Мы создали этого бота, чтобы вы могли спланировать "
        "свой идеальный отдых заранее и без лишних звонков. Что мы предлагаем:\n\n"
        "✨ Уютные VIP-кабинки и комфортные столики в общем зале\n"
        "🔥 Быстрое бронирование столика онлайн за 1 минуту\n"
        "🍽 Возможность предзаказа блюд — еда будет готова точно к вашему приходу\n"
        "💳 Безопасная онлайн-оплата депозита прямо в чате\n\n"
        "📍 <b>Наш адрес:</b> ул. Набережная, д. 25\n"
        "⏰ <b>Время работы:</b> Ежедневно с 12:00 до 22:00\n"
        "🌐 <b>Наш сайт:</b> <a href='https://example.com'>restaurant.ru</a>\n\n"
        "<i>Ждём вас в гости за незабываемыми гастрономическими впечатлениями! ❤️</i>",
        reply_markup=reply_kb(),
        disable_web_page_preview=True,
    )
