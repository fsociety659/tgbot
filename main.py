import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault
from database.connections import init_db
from config import TOKEN
from handlers.commands import router as cmd_router
from handlers.booking_fsm import router as booking_router
from handlers.payment import router as payment_router
from handlers.inline_mode import router as inline_router
from handlers.food_order import router as food_router


def setup_logger():
    log_format = (
        "\033[1;36m%(asctime)s\033[0m | "
        "\033[1;35m%(levelname)-4s\033[0m | "
        "\033[1;32m%(name)s\033[0m -> "
        "%(message)s"
    )
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def on_startup(dispatcher: Dispatcher):
    logger = logging.getLogger("Init")
    logger.info("Подключение к базе данных SQLite...")
    await init_db()
    logger.info("База данных успешно инициализирована.")
    logger.info("Бот успешно запущен и готов к работе!")


async def main():
    setup_logger()
    logger = logging.getLogger("Core")
    logger.info("Запуск конфигурации приложения...")

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    async def set_commands(bot):
        commands = [
            BotCommand(
                command="start", description="🔄 Перезапустить бота / Главное меню"
            ),
            BotCommand(command="help", description="❓ Помощь и правила ресторана"),
            BotCommand(command="about", description="ℹ️ О нашем ресторане"),
        ]
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

    dp.startup.register(on_startup)

    logger.info("Регистрация хэндлеров и роутеров...")
    dp.include_router(cmd_router)
    dp.include_router(booking_router)
    dp.include_router(payment_router)
    dp.include_router(food_router)
    dp.include_router(inline_router)

    logger.info("Удаление вебхуков и запуск опроса серверов Telegram (Polling)...")
    await bot.delete_webhook(drop_pending_updates=True)

    await set_commands(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Сессия бота закрыта. Работа завершена.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger("Core").warning("Бот принудительно остановлен!")
