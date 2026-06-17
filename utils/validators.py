from config import DB_URL
import aiosqlite

TIME_SLOTS = ["12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
LOCATIONS = ["У окна", "В зале", "VIP кабинка"]
TOTAL_SLOTS = len(TIME_SLOTS) * len(LOCATIONS)

PEAK_HOURS = {"18:00", "20:00", "22:00"}

TABLE_PRICES = {
    "У окна": 500,
    "В зале": 500,
    "VIP кабинка": 1500,
}

PEAK_PRICE = 300
GUEST_PRICE = 100


def calculate_booking_price(
    table_location: str, booking_time: str, guests_count: int
) -> int:
    price = TABLE_PRICES.get(table_location, 500)
    if booking_time in PEAK_HOURS:
        price += PEAK_PRICE
    price += guests_count * GUEST_PRICE
    return price


async def get_booked_dates_from_db() -> set[str]:
    async with aiosqlite.connect(DB_URL) as db:
        cursor = await db.execute(
            """
            SELECT booking_date, COUNT(DISTINCT booking_time || '_' || table_location) as cnt
            FROM bookings
            GROUP BY booking_date
            """
        )
        rows = await cursor.fetchall()
    return {row[0] for row in rows if row[1] >= TOTAL_SLOTS}


async def get_booked_times_for_date(booking_date: str) -> set[str]:
    async with aiosqlite.connect(DB_URL) as db:
        cursor = await db.execute(
            """
            SELECT booking_time, COUNT(DISTINCT table_location) as cnt
            FROM bookings
            WHERE booking_date = ?
            GROUP BY booking_time
            """,
            (booking_date,),
        )
        rows = await cursor.fetchall()
    total_locations = len(LOCATIONS)
    return {row[0] for row in rows if row[1] >= total_locations}


async def get_booked_locations_for_slot(
    booking_date: str, booking_time: str
) -> set[str]:
    async with aiosqlite.connect(DB_URL) as db:
        cursor = await db.execute(
            """
            SELECT table_location
            FROM bookings
            WHERE booking_date = ? AND booking_time = ?
            """,
            (booking_date, booking_time),
        )
        rows = await cursor.fetchall()
    return {row[0] for row in rows}
