from datetime import datetime, timedelta
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.validators import get_booked_dates_from_db, TABLE_PRICES, PEAK_HOURS

MENU = {
    "fish": [
        ("🐟 Стейк из лосося", 850),
        ("🐠 Дорадо на гриле", 920),
        ("🦈 Тунец с овощами", 990),
        ("🦐 Креветки в соусе", 780),
        ("🐡 Форель запечённая", 860),
    ],
    "meat": [
        ("🥩 Стейк Рибай", 1350),
        ("🍖 Медальоны из говядины", 980),
        ("🍗 Куриное филе на гриле", 750),
        ("🥓 Свиные рёбра BBQ", 890),
        ("🫕 Говяжьи щёчки", 1100),
    ],
    "drinks": [
        ("🍋 Домашний лимонад", 280),
        ("🫐 Морс из ягод", 220),
        ("🍵 Чай с травами", 180),
        ("☕ Американо", 200),
        ("🥤 Свежевыжатый сок", 320),
    ],
}


def food_keyboard(
    category: str, cart: dict, next_btn_text: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, price in MENU[category]:
        count = cart.get(name, 0)
        label = f"{'✅ ' if count else ''}{name} — {price}₽{f' (x{count})' if count else ''}"
        builder.add(
            InlineKeyboardButton(text=label, callback_data=f"food_{category}_{name}")
        )
    builder.add(
        InlineKeyboardButton(text=next_btn_text, callback_data=f"food_next_{category}")
    )
    builder.add(
        InlineKeyboardButton(text="❌ Отменить заказ", callback_data="food_cancel")
    )
    builder.adjust(1)
    return builder.as_markup()


def booking_choice_keyboard(bookings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for b in bookings:
        builder.add(
            InlineKeyboardButton(
                text=f"📅 {b['booking_date']}, {b['booking_time']} ({b['table_location']})",
                callback_data=f"preorder_booking_{b['id']}",
            )
        )
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="food_cancel"))
    builder.adjust(1)
    return builder.as_markup()


def order_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Да, всё верно", callback_data="food_confirm_yes"),
        InlineKeyboardButton(text="❌ Нет, изменить", callback_data="food_confirm_no"),
    )
    builder.adjust(1)
    return builder.as_markup()


def food_payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="💳 Оплатить онлайн", callback_data="food_pay_online"
        ),
        InlineKeyboardButton(
            text="💵 Оплатить на месте", callback_data="food_pay_venue"
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def number_of_guests() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="👤 1 человек", callback_data="guests_1"),
        InlineKeyboardButton(text="👥 2 человека", callback_data="guests_2"),
        InlineKeyboardButton(text="👨‍👩‍👦 3 человека", callback_data="guests_3"),
        InlineKeyboardButton(text="👨‍👩‍👧‍👦 4 человека", callback_data="guests_4"),
    )
    builder.add(
        InlineKeyboardButton(text="❌ Отмена бронирования", callback_data="cancel")
    )
    builder.adjust(1)
    return builder.as_markup()


def location_keyboard(booked_locations: set = None) -> InlineKeyboardMarkup:
    if booked_locations is None:
        booked_locations = set()

    builder = InlineKeyboardBuilder()

    locations = [
        ("У окна", "window", "🪟"),
        ("В зале", "hall", "🎯"),
        ("VIP кабинка", "vip", "👑"),
    ]
    for name, key, emoji in locations:
        if name in booked_locations:
            builder.add(
                InlineKeyboardButton(
                    text=f"🔴 {name} (Занято)", callback_data=f"location_booked_{key}"
                )
            )
        else:
            price = TABLE_PRICES[name]
            builder.add(
                InlineKeyboardButton(
                    text=f"{emoji} {name} — {price}₽", callback_data=f"location_{key}"
                )
            )

    builder.add(
        InlineKeyboardButton(text="❌ Отмена бронирования", callback_data="cancel")
    )
    builder.adjust(1)
    return builder.as_markup()


def confirmation_keyboard(total_price: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=f"✅ Подтвердить ({total_price}₽)", callback_data="confirm_yes"
        ),
        InlineKeyboardButton(text="❌ Нет, начать заново", callback_data="confirm_no"),
    )
    builder.add(InlineKeyboardButton(text="Отменить", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="💳 Внести депозит (Онлайн)", callback_data="pay_online"
        ),
        InlineKeyboardButton(
            text="💵 Оплата на месте в ресторане", callback_data="pay_at_venue"
        ),
    )
    builder.add(
        InlineKeyboardButton(text="❌ Отмена бронирования", callback_data="cancel")
    )
    builder.adjust(1)
    return builder.as_markup()


async def get_dates_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    today = datetime.now()
    booked_dates = await get_booked_dates_from_db()

    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime("%d.%m")
        db_date_str = date.strftime("%d.%m.%Y")

        if db_date_str in booked_dates:
            label = f"🔴 {date_str} (Занято)"
            callback_data = f"day_booked_{db_date_str}"
        else:
            callback_data = f"book_date_{db_date_str}"
            if i == 0:
                label = f"🔵 Сегодня ({date_str})"
            elif i == 1:
                label = f"🟢 Завтра ({date_str})"
            else:
                label = f"🟢 {date_str}"

        builder.add(InlineKeyboardButton(text=label, callback_data=callback_data))

    builder.add(
        InlineKeyboardButton(text="❌ Отмена бронирования", callback_data="cancel")
    )
    builder.adjust(2)
    return builder.as_markup()


def get_time_keyboard(booked_times: set = None) -> InlineKeyboardMarkup:
    if booked_times is None:
        booked_times = set()

    time_slots = ["12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
    builder = InlineKeyboardBuilder()

    for slot in time_slots:
        if slot in booked_times:
            builder.add(
                InlineKeyboardButton(
                    text=f"🔴 {slot}", callback_data=f"time_booked_{slot}"
                )
            )
        else:
            peak = " 🔥+300₽" if slot in PEAK_HOURS else ""
            builder.add(
                InlineKeyboardButton(
                    text=f"{slot}{peak}", callback_data=f"book_time_{slot}"
                )
            )

    builder.add(
        InlineKeyboardButton(text="❌ Отмена бронирования", callback_data="cancel")
    )
    builder.adjust(2)
    return builder.as_markup()
