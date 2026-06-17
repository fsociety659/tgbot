import aiosqlite
import json
from config import DB_URL


async def create_booking(
    user_id: int,
    booking_date: str,
    booking_time: str,
    guests_count: int,
    table_location: str,
    is_paid: int = 0,
    total_price: int = 0,
):
    async with aiosqlite.connect(DB_URL) as db:
        cursor = await db.execute(
            "INSERT INTO bookings (user_id, booking_date, booking_time, guests_count, table_location, is_paid, total_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                booking_date,
                booking_time,
                guests_count,
                table_location,
                is_paid,
                total_price,
            ),
        )
        await db.commit()
        cursor = await db.execute("SELECT last_insert_rowid()")
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_user_bookings(user_id: int):
    async with aiosqlite.connect(DB_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        return await cursor.fetchall()


async def get_active_user_bookings(user_id: int):
    async with aiosqlite.connect(DB_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM bookings
            WHERE user_id = ?
            AND date(substr(booking_date,7,4)||'-'||substr(booking_date,4,2)||'-'||substr(booking_date,1,2)) >= date('now')
            ORDER BY booking_date ASC
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_latest_booking(user_id: int):
    async with aiosqlite.connect(DB_URL) as db:
        cursor = await db.execute(
            "SELECT id, booking_date, booking_time, guests_count, table_location FROM bookings WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        )
        return await cursor.fetchone()


async def check_availability(
    booking_date: str, booking_time: str, table_location: str, guests_count: int
) -> bool:
    async with aiosqlite.connect(DB_URL) as db:
        cursor = await db.execute(
            "SELECT capacity FROM tables WHERE location = ?", (table_location,)
        )
        table = await cursor.fetchone()
        if not table or guests_count > table[0]:
            return False

        cursor = await db.execute(
            "SELECT COUNT(*) FROM bookings WHERE booking_date = ? AND booking_time = ? AND table_location = ?",
            (booking_date, booking_time, table_location),
        )
        count = await cursor.fetchone()
        return count[0] == 0


async def delete_booking(booking_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_URL) as db:
        cursor = await db.execute(
            "SELECT user_id FROM bookings WHERE id = ?", (booking_id,)
        )
        booking = await cursor.fetchone()
        if not booking or booking[0] != user_id:
            return False

        await db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        await db.execute("DELETE FROM food_orders WHERE booking_id = ?", (booking_id,))
        await db.commit()
        return True


async def get_booking_by_id(booking_id: int):
    async with aiosqlite.connect(DB_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        return await cursor.fetchone()


async def create_food_order(
    booking_id: int,
    user_id: int,
    items: list,
    total_price: int,
    is_paid: int = 0,
):
    async with aiosqlite.connect(DB_URL) as db:
        await db.execute(
            "INSERT INTO food_orders (booking_id, user_id, items, total_price, is_paid) VALUES (?, ?, ?, ?, ?)",
            (
                booking_id,
                user_id,
                json.dumps(items, ensure_ascii=False),
                total_price,
                is_paid,
            ),
        )
        await db.commit()


async def get_active_bookings_without_food(user_id: int):
    async with aiosqlite.connect(DB_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT b.* FROM bookings b
            LEFT JOIN food_orders f ON f.booking_id = b.id
            WHERE b.user_id = ?
            AND date(substr(b.booking_date,7,4)||'-'||substr(b.booking_date,4,2)||'-'||substr(b.booking_date,1,2)) >= date('now')
            AND f.id IS NULL
            ORDER BY b.booking_date ASC
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_food_order_by_booking(booking_id: int):
    async with aiosqlite.connect(DB_URL) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM food_orders WHERE booking_id = ?", (booking_id,)
        )
        return await cursor.fetchone()


async def update_food_order_payment(booking_id: int, is_paid: int):
    async with aiosqlite.connect(DB_URL) as db:
        await db.execute(
            "UPDATE food_orders SET is_paid = ? WHERE booking_id = ?",
            (is_paid, booking_id),
        )
        await db.commit()
