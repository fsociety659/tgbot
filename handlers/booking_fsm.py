import re
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keybaords.inline import (
    confirmation_keyboard,
    get_dates_keyboard,
    get_time_keyboard,
    location_keyboard,
    number_of_guests,
    payment_keyboard,
)
from keybaords.reply import reply_kb
from middlewares.check_slot import validate_slot
from states.booking import BookingStates
from utils.validators import (
    get_booked_times_for_date,
    get_booked_locations_for_slot,
    calculate_booking_price,
)

router = Router()


@router.message(Command("book"))
@router.message(F.text == "📅 Забронировать столик")
async def start_booking(message: Message, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_date)
    await message.answer(
        "<b>Шаг 1 из 4: Выберите дату</b>\n\nПожалуйста, выберите удобный день:",
        reply_markup=await get_dates_keyboard(),
    )


@router.callback_query(BookingStates.waiting_for_date, F.data.startswith("day_booked_"))
async def process_booked_date(callback: CallbackQuery):
    date_str = callback.data.replace("day_booked_", "")
    await callback.answer(
        f"❌ На {date_str} все столики заняты. Выберите другую дату.",
        show_alert=True,
    )


@router.callback_query(BookingStates.waiting_for_date, F.data.startswith("book_date_"))
async def process_date_selection(callback: CallbackQuery, state: FSMContext):
    formatted_date = callback.data.replace("book_date_", "")
    await state.update_data(booking_date=formatted_date)
    await state.set_state(BookingStates.waiting_for_time)

    booked_times = await get_booked_times_for_date(formatted_date)

    await callback.message.delete()
    await callback.message.answer(
        f"📅 Вы выбрали дату: <b>{formatted_date}</b>\n\n"
        "<b>Шаг 2 из 4: Выберите время</b>\n"
        "🔥 — час пик, доплата 300₽\n\n"
        "Пожалуйста, выберите удобный временной слот:",
        reply_markup=get_time_keyboard(booked_times),
    )
    await callback.answer()


@router.callback_query(
    BookingStates.waiting_for_time, F.data.startswith("time_booked_")
)
async def process_booked_time(callback: CallbackQuery):
    time_str = callback.data.replace("time_booked_", "")
    await callback.answer(
        f"❌ Время {time_str} уже занято. Выберите другой слот.",
        show_alert=True,
    )


@router.callback_query(BookingStates.waiting_for_time, F.data.startswith("book_time_"))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.replace("book_time_", "")
    if not re.match(r"^\d{2}:\d{2}$", time_str):
        await callback.answer("Некорректное время", show_alert=True)
        return

    data = await state.get_data()
    booking_date = data.get("booking_date")
    if booking_date == datetime.now().strftime("%d.%m.%Y"):
        selected_dt = datetime.strptime(f"{booking_date} {time_str}", "%d.%m.%Y %H:%M")
        now_truncated = datetime.now().replace(second=0, microsecond=0)
        if selected_dt < now_truncated:
            await callback.answer(
                "Нельзя забронировать столик на прошедшее время",
                show_alert=True,
            )
            return

    await state.update_data(booking_time=time_str)
    await state.set_state(BookingStates.waiting_for_guests)

    await callback.message.delete()
    await callback.message.answer(
        f"⏰ Вы выбрали время: <b>{time_str}</b>\n\n"
        f"📅 Дата: <b>{booking_date}</b>\n\n"
        "<b>Шаг 3 из 4: Выберите количество гостей</b>\n"
        "Каждый гость +100₽ к стоимости:",
        reply_markup=number_of_guests(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("guests_"), BookingStates.waiting_for_guests)
async def process_guests_selection(callback: CallbackQuery, state: FSMContext):
    guests_count = int(callback.data.split("_")[1])
    await state.update_data(guests_count=guests_count)
    await state.set_state(BookingStates.waiting_for_location)

    data = await state.get_data()
    booked_locations = await get_booked_locations_for_slot(
        data.get("booking_date"), data.get("booking_time")
    )

    await callback.message.delete()
    await callback.message.answer(
        f"👥 Вы выбрали {guests_count} гостей.\n\n"
        f"📅 Дата: <b>{data.get('booking_date')}</b>\n"
        f"⏰ Время: <b>{data.get('booking_time')}</b>\n\n"
        "<b>Шаг 4 из 4: Выберите место</b>\n"
        "👑 VIP кабинка — приватное пространство:",
        reply_markup=location_keyboard(booked_locations),
    )


@router.callback_query(
    F.data.startswith("location_booked_"), BookingStates.waiting_for_location
)
async def process_booked_location(callback: CallbackQuery):
    if "window" in callback.data:
        loc = "У окна"
    elif "vip" in callback.data:
        loc = "VIP кабинка"
    else:
        loc = "В зале"
    await callback.answer(
        f"❌ Место «{loc}» уже занято на это время. Выберите другое.",
        show_alert=True,
    )


@router.callback_query(
    F.data.startswith("location_"), BookingStates.waiting_for_location
)
async def process_location_selection(callback: CallbackQuery, state: FSMContext):
    loc_key = callback.data.split("_")[1]
    if loc_key == "window":
        location = "У окна"
    elif loc_key == "vip":
        location = "VIP кабинка"
    else:
        location = "В зале"

    await state.update_data(table_location=location)
    await state.set_state(BookingStates.waiting_for_confirmation)

    data = await state.get_data()
    total_price = calculate_booking_price(
        location, data.get("booking_time"), int(data.get("guests_count"))
    )
    await state.update_data(total_price=total_price)

    await callback.message.delete()
    await callback.message.answer(
        f"Проверьте детали бронирования:\n\n"
        f"📅 Дата: <b>{data.get('booking_date')}</b>\n"
        f"⏰ Время: <b>{data.get('booking_time')}</b>\n"
        f"👥 Гостей: <b>{data.get('guests_count')}</b>\n"
        f"📍 Место: <b>{location}</b>\n\n"
        f"💰 <b>Итого к оплате: {total_price}₽</b>\n\n"
        "Если всё верно — подтвердите бронирование:",
        reply_markup=confirmation_keyboard(total_price),
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_yes", BookingStates.waiting_for_confirmation)
async def process_confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    is_available, message_text = await validate_slot(
        data.get("booking_date"),
        data.get("booking_time"),
        data.get("table_location"),
        int(data.get("guests_count")),
    )

    if not is_available:
        booked_times = await get_booked_times_for_date(data.get("booking_date"))
        await state.set_state(BookingStates.waiting_for_time)
        await callback.message.delete()
        await callback.message.answer(
            f"❌ <b>Этот слот уже недоступен:</b>\n{message_text}\n\n"
            f"📅 Выбранная дата: <b>{data.get('booking_date')}</b>\n"
            "Пожалуйста, выберите другое удобное время:",
            reply_markup=get_time_keyboard(booked_times),
        )
        await callback.answer()
        return

    await state.set_state(BookingStates.waiting_for_payment)
    await callback.message.delete()
    await callback.message.answer(
        f"📋 <b>Подтверждение принято!</b>\n\n"
        f"📅 Дата: <b>{data.get('booking_date')}</b>\n"
        f"⏰ Время: <b>{data.get('booking_time')}</b>\n"
        f"👥 Гостей: <b>{data.get('guests_count')}</b>\n"
        f"📍 Место: <b>{data.get('table_location')}</b>\n"
        f"💰 Сумма: <b>{data.get('total_price')}₽</b>\n\n"
        "💳 <b>Выберите способ оплаты:</b>",
        reply_markup=payment_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_no", BookingStates.waiting_for_confirmation)
async def process_confirm_no(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_date)
    await callback.message.delete()
    await callback.message.answer(
        "Хорошо, начнем заново. Пожалуйста, выберите дату:",
        reply_markup=await get_dates_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def process_cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🚫 Бронирование отменено.\n\nЕсли захотите забронировать столик — просто нажмите кнопку ниже.",
        reply_markup=reply_kb(),
    )


@router.message(F.text == "❌ Отмена")
async def process_cancel_message(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🚫 Бронирование отменено.\n\nЕсли захотите забронировать столик — просто нажмите кнопку ниже.",
        reply_markup=reply_kb(),
    )
