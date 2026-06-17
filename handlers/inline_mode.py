from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from database.requests import get_latest_booking

router = Router()


@router.inline_query()
async def process_inline_query(inline_query: InlineQuery):
    user_id = inline_query.from_user.id

    booking = await get_latest_booking(user_id)

    results = []

    if booking:
        b_id, b_date, b_time, b_guests, b_loc = booking

        share_text = (
            f"🏛 <b>Я забронировал столик в ресторане!</b>\n\n"
            f"📅 <b>Дата:</b> {b_date}\n"
            f"⏰ <b>Время:</b> {b_time}\n"
            f"📍 <b>Место:</b> {b_loc}\n"
            f"👥 <b>Иду один / с компанией:</b> {b_guests} чел.\n\n"
            f"<i>Номер брони: #{b_id}</i>"
        )

        results.append(
            InlineQueryResultArticle(
                id=str(b_id),
                title="Поделиться бронированием 📅",
                description=f"Столик на {b_date} в {b_time} ({b_loc})",
                input_message_content=InputTextMessageContent(
                    message_text=share_text, parse_mode="HTML"
                ),
            )
        )
    else:
        results.append(
            InlineQueryResultArticle(
                id="no_bookings",
                title="У вас нет активных бронирований 🤷‍♂️",
                description="Сначала забронируйте столик через бота.",
                input_message_content=InputTextMessageContent(
                    message_text="Привет! Я хотел поделиться бронью, но еще не успел заказать столик."
                ),
            )
        )

    await inline_query.answer(results, is_personal=True, cache_time=5)
