from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    LabeledPrice,
    PreCheckoutQuery,
    ContentType,
)
from aiogram.fsm.context import FSMContext

from states.booking import BookingStates
from keybaords.reply import reply_kb
from database.requests import create_booking
from config import PROVIDER_TOKEN

router = Router()


@router.callback_query(BookingStates.waiting_for_payment, F.data == "pay_at_venue")
async def process_pay_at_venue(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id

    booking_id = await create_booking(
        user_id=user_id,
        booking_date=data.get("booking_date"),
        booking_time=data.get("booking_time"),
        guests_count=int(data.get("guests_count")),
        table_location=data.get("table_location"),
        is_paid=0,
        total_price=int(data.get("total_price", 0)),
    )

    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        f"🤝 <b>Бронирование успешно оформлено!</b>\n"
        f"🎟️ Номер вашей брони: <b>№{booking_id}</b>\n"
        f"───────────────────\n"
        f"📅 <b>Дата:</b> {data.get('booking_date')}\n"
        f"⏰ <b>Время:</b> {data.get('booking_time')}\n"
        f"👥 <b>Гостей:</b> {data.get('guests_count')} чел.\n"
        f"📍 <b>Локация:</b> {data.get('table_location')}\n"
        f"💵 <b>Оплата при визите:</b> {data.get('total_price')}₽\n"
        f"───────────────────\n"
        f"🍽️ Столик закреплен за вами. Ждём вас в гости!",
        reply_markup=reply_kb(),
    )


@router.callback_query(BookingStates.waiting_for_payment, F.data == "pay_online")
async def process_pay_online_invoice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.delete()

    amount = int(data.get("total_price", 500)) * 100
    prices = [LabeledPrice(label="Депозит за бронирование столика", amount=amount)]

    await callback.message.answer_invoice(
        title="💳 Депозит за бронирование",
        description=f"Бронь столика на {data.get('booking_date')} в {data.get('booking_time')}",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        payload="online_booking_deposit_payload",
        start_parameter="booking-pay-deposit",
    )


@router.pre_checkout_query(BookingStates.waiting_for_payment)
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(
    BookingStates.waiting_for_payment, F.content_type == ContentType.SUCCESSFUL_PAYMENT
)
async def process_successful_payment(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id

    booking_id = await create_booking(
        user_id=user_id,
        booking_date=data.get("booking_date"),
        booking_time=data.get("booking_time"),
        guests_count=int(data.get("guests_count")),
        table_location=data.get("table_location"),
        is_paid=1,
        total_price=int(data.get("total_price", 0)),
    )

    await state.clear()
    await message.answer(
        f"🎉 <b>Депозит успешно оплачен!</b>\n"
        f"🎟️ Номер вашей брони: <b>№{booking_id}</b>\n"
        f"───────────────────\n"
        f"📅 <b>Дата:</b> {data.get('booking_date')}\n"
        f"⏰ <b>Время:</b> {data.get('booking_time')}\n"
        f"👥 <b>Гостей:</b> {data.get('guests_count')} чел.\n"
        f"📍 <b>Локация:</b> {data.get('table_location')}\n"
        f"💳 <b>Статус оплаты:</b> Внесен депозит {data.get('total_price')}₽\n"
        f"───────────────────\n"
        f"✨ Бронирование подтверждено. С нетерпением ждём вас!",
        reply_markup=reply_kb(),
    )


@router.callback_query(F.data == "cancel", BookingStates.waiting_for_payment)
async def process_cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ <b>Бронирование отменено.</b>\n\n"
        "Если вы захотите выбрать другое время или локацию — просто нажмите кнопку ниже 👇",
        reply_markup=reply_kb(),
    )
