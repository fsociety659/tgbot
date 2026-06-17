import aiosqlite
from config import DB_URL


async def init_db():
    async with aiosqlite.connect(DB_URL) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                booking_date TEXT NOT NULL,
                booking_time TEXT NOT NULL,
                guests_count INTEGER NOT NULL,
                table_location TEXT NOT NULL,
                is_paid INTEGER NOT NULL DEFAULT 0,
                total_price INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                is_available INTEGER NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS food_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                items TEXT NOT NULL,
                total_price INTEGER NOT NULL DEFAULT 0,
                is_paid INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (booking_id) REFERENCES bookings(id)
            )
            """
        )
        await db.commit()

        cursor = await db.execute("SELECT COUNT(*) FROM tables")
        count = await cursor.fetchone()
        if count[0] == 0:
            await db.execute(
                "INSERT INTO tables (location, capacity, is_available) VALUES (?, ?, ?)",
                ("У окна", 4, 1),
            )
            await db.execute(
                "INSERT INTO tables (location, capacity, is_available) VALUES (?, ?, ?)",
                ("В зале", 6, 1),
            )
            await db.execute(
                "INSERT INTO tables (location, capacity, is_available) VALUES (?, ?, ?)",
                ("VIP кабинка", 4, 1),
            )
            await db.commit()
