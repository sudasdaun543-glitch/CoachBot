import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.handlers import admin, stats, user
from bot.middlewares.admin import AdminMiddleware

logger = logging.getLogger(__name__)


async def main() -> None:
    """Точка входа в бота."""
    logger.info("Инициализация базы данных...")
    await init_db()

    logger.info("Создание бота и диспетчера...")
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Подключаем middleware
    dp.message.middleware(AdminMiddleware())

    # Подключаем роутеры
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(stats.router)

    logger.info("Бот запущен и готов к работе!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
