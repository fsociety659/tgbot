from database.requests import check_availability


async def validate_slot(
    booking_date: str, booking_time: str, table_location: str, guests_count: int
) -> tuple[bool, str]:
    try:
        is_available = await check_availability(
            booking_date, booking_time, table_location, guests_count
        )
        if is_available:
            return True, "Столик доступен!"
        else:
            return (
                False,
                "❌ Столик на выбранное время уже занят или не подходит по вместимости.",
            )
    except Exception as e:
        return False, f"❌ Ошибка проверки доступности: {str(e)}"
