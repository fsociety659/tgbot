from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
    LabeledPrice,
    PreCheckoutQuery,
    ContentType,
)

from keybaords.inline import (
    booking_choice_keyboard,
    food_keyboard,
    order_confirm_keyboard,
    food_payment_keyboard,
    MENU,
)
from keybaords.reply import reply_kb
from states.booking import FoodOrderStates
from database.requests import get_active_bookings_without_food, create_food_order
from config import PROVIDER_TOKEN

router = Router()


def format_cart(cart: dict, status: str = "pending") -> str:
    if not cart:
        return
    lines = []
    total = 0
    all_items = {name: price for cat in MENU.values() for name, price in cat}
    for name, count in cart.items():
        price = all_items.get(name, 0)
        subtotal = price * count
        total += subtotal
        lines.append(f"• {name} x{count} — {subtotal}₽")

    lines.append("\n───────────────────")
    if status == "online":
        lines.append(f"💳 <b>Итого оплачено: {total}₽</b>")
    elif status == "venue":
        lines.append(f"💵 <b>Сумма к оплате при визите: {total}₽</b>")
    else:
        lines.append(f"💰 <b>Итого к оплате за еду: {total}₽</b>")

    return "\n".join(lines)


def get_cart_total(cart: dict) -> int:
    all_items = {name: price for cat in MENU.values() for name, price in cat}
    return sum(all_items.get(name, 0) * count for name, count in cart.items())


@router.message(F.text == "🍽️ Предзаказ еды")
async def start_food_order(message: Message, state: FSMContext):
    bookings = await get_active_bookings_without_food(message.from_user.id)

    if not bookings:
        await message.answer(
            "📋 У вас нет активных бронирований или ко всем уже оформлен предзаказ.\n\n"
            "Сначала забронируйте столик, затем сделайте предзаказ еды!",
            reply_markup=reply_kb(),
        )
        return

    await state.set_state(FoodOrderStates.choosing_booking)
    await message.answer(
        "🍽️ <b>Предзаказ еды</b>\n\n"
        "Выберите бронирование к которому хотите привязать заказ:",
        reply_markup=booking_choice_keyboard(bookings),
    )


@router.callback_query(
    FoodOrderStates.choosing_booking, F.data.startswith("preorder_booking_")
)
async def process_booking_choice(callback: CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.replace("preorder_booking_", ""))
    await state.update_data(booking_id=booking_id, cart={})
    await state.set_state(FoodOrderStates.choosing_fish)

    await callback.message.delete()
    await callback.message.answer(
        "🐟 <b>Шаг 1 из 3: Рыбные блюда</b>\n\n"
        "Нажимайте на блюда чтобы добавить в корзину.\n"
        "Когда закончите — нажмите <b>Далее</b>:",
        reply_markup=food_keyboard("fish", {}, "Далее ➡️"),
    )
    await callback.answer()


@router.callback_query(FoodOrderStates.choosing_fish, F.data.startswith("food_fish_"))
async def process_fish_choice(callback: CallbackQuery, state: FSMContext):
    name = callback.data.replace("food_fish_", "")
    data = await state.get_data()
    cart = data.get("cart", {})
    cart[name] = cart.get(name, 0) + 1
    await state.update_data(cart=cart)
    await callback.message.edit_reply_markup(
        reply_markup=food_keyboard("fish", cart, "Далее ➡️")
    )
    await callback.answer(f"✅ {name} добавлено!")


@router.callback_query(FoodOrderStates.choosing_fish, F.data == "food_next_fish")
async def fish_to_meat(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(FoodOrderStates.choosing_meat)
    await callback.message.delete()
    await callback.message.answer(
        "🥩 <b>Шаг 2 из 3: Мясные блюда</b>\n\n"
        "Нажимайте на блюда чтобы добавить в корзину.\n"
        "Когда закончите — нажмите <b>Далее</b>:",
        reply_markup=food_keyboard("meat", data.get("cart", {}), "Далее ➡️"),
    )
    await callback.answer()


@router.callback_query(FoodOrderStates.choosing_meat, F.data.startswith("food_meat_"))
async def process_meat_choice(callback: CallbackQuery, state: FSMContext):
    name = callback.data.replace("food_meat_", "")
    data = await state.get_data()
    cart = data.get("cart", {})
    cart[name] = cart.get(name, 0) + 1
    await state.update_data(cart=cart)
    await callback.message.edit_reply_markup(
        reply_markup=food_keyboard("meat", cart, "Далее ➡️")
    )
    await callback.answer(f"✅ {name} добавлено!")


@router.callback_query(FoodOrderStates.choosing_meat, F.data == "food_next_meat")
async def meat_to_drinks(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(FoodOrderStates.choosing_drinks)
    await callback.message.delete()
    await callback.message.answer(
        "🥤 <b>Шаг 3 из 3: Напитки</b>\n\n"
        "Нажимайте на напитки, чтобы добавить их в корзину.\n"
        "Когда закончите — нажмите <b>Итог</b> 👇",
        reply_markup=food_keyboard("drinks", data.get("cart", {}), "Итог 🛒"),
    )
    await callback.answer()


@router.callback_query(
    FoodOrderStates.choosing_drinks, F.data.startswith("food_drinks_")
)
async def process_drink_choice(callback: CallbackQuery, state: FSMContext):
    name = callback.data.replace("food_drinks_", "")
    data = await state.get_data()
    cart = data.get("cart", {})
    cart[name] = cart.get(name, 0) + 1
    await state.update_data(cart=cart)
    await callback.message.edit_reply_markup(
        reply_markup=food_keyboard("drinks", cart, "Итог 🛒")
    )
    await callback.answer(f"✅ {name} добавлено!")


@router.callback_query(FoodOrderStates.choosing_drinks, F.data == "food_next_drinks")
async def show_cart(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})

    if not cart:
        await callback.answer(
            "⚠️ Вы ничего не выбрали! Добавьте хотя бы одно блюдо.", show_alert=True
        )
        return

    await state.set_state(FoodOrderStates.confirming_order)
    await callback.message.delete()
    await callback.message.answer(
        f"🛒 <b>Ваш предзаказ сформирован:</b>\n\n"
        f"{format_cart(cart, status='pending')}\n\n"
        f"Пожалуйста, проверьте позиции. Всё верно?",
        reply_markup=order_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(FoodOrderStates.confirming_order, F.data == "food_confirm_yes")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FoodOrderStates.paying_order)
    await callback.message.delete()
    await callback.message.answer(
        "💳 <b>Выберите удобный способ оплаты предзаказа:</b>",
        reply_markup=food_payment_keyboard(),
    )
    await callback.answer()


@router.callback_query(FoodOrderStates.confirming_order, F.data == "food_confirm_no")
async def edit_order(callback: CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await state.set_state(FoodOrderStates.choosing_fish)
    await callback.message.delete()
    await callback.message.answer(
        "🗑 *Корзина очищена.* Давайте соберем заказ заново!\n\n"
        "🐟 <b>Шаг 1 из 3: Рыбные блюда</b>\n\n"
        "Выберите позиции из меню ниже:",
        reply_markup=food_keyboard("fish", {}, "Далее ➡️"),
    )
    await callback.answer()


@router.callback_query(FoodOrderStates.paying_order, F.data == "food_pay_online")
async def food_pay_online(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    total = get_cart_total(cart)
    booking_id = data.get("booking_id")

    await callback.message.delete()
    prices = [LabeledPrice(label="Полная оплата предзаказа", amount=total * 100)]
    await callback.message.answer_invoice(
        title="🛒 Оплата предзаказа еды",
        description=f"Полная оплата выбранных блюд к вашей брони №{booking_id}",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        payload=f"food_order_{booking_id}",
        start_parameter="food-pay",
    )
    await callback.answer()


@router.pre_checkout_query(lambda q: q.invoice_payload.startswith("food_order_"))
async def food_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(
    FoodOrderStates.paying_order, F.content_type == ContentType.SUCCESSFUL_PAYMENT
)
async def food_successful_payment(message: Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    total = get_cart_total(cart)
    booking_id = data.get("booking_id")

    await create_food_order(
        booking_id=booking_id,
        user_id=message.from_user.id,
        items=list(cart.items()),
        total_price=total,
        is_paid=1,
    )

    await state.clear()
    await message.answer(
        f"🎉 <b>Предзаказ успешно оплачен!</b>\n\n"
        f"📋 <b>Ваш чек (Бронь №{booking_id}):</b>\n"
        f"{format_cart(cart, status='online')}\n\n"
        f"✅ Транзакция прошла успешно. Ждем вас в ресторане!",
        reply_markup=reply_kb(),
    )


@router.callback_query(FoodOrderStates.paying_order, F.data == "food_pay_venue")
async def food_pay_at_venue(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    total = get_cart_total(cart)
    booking_id = data.get("booking_id")

    await create_food_order(
        booking_id=booking_id,
        user_id=callback.from_user.id,
        items=list(cart.items()),
        total_price=total,
        is_paid=0,
    )

    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        f"🤝 <b>Предзаказ успешно оформлен!</b>\n\n"
        f"📋 <b>Состав заказа (Бронь №{booking_id}):</b>\n"
        f"{format_cart(cart, status='venue')}\n\n"
        f"🍽️ Блюда будут готовы к вашему приходу. Назовите номер брони официанту!",
        reply_markup=reply_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "food_cancel")
async def cancel_food_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Предзаказ отменен. Корзина сброшена.\n\nВы вернулись в главное меню 👇",
        reply_markup=reply_kb(),
    )
    await callback.answer()
