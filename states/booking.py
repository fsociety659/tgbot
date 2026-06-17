from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_guests = State()
    waiting_for_location = State()
    waiting_for_confirmation = State()
    waiting_for_payment = State()


class FoodOrderStates(StatesGroup):
    choosing_booking = State()
    choosing_fish = State()
    choosing_meat = State()
    choosing_drinks = State()
    confirming_order = State()
    paying_order = State()
