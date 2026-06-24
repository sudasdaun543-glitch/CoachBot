"""
Скрипт для запуска и бота, и веб-сервера одновременно.
Используется на Railway (один сервис для всего).
"""
import asyncio
import logging
import sys
import threading

# Настраиваем логгирование ДО импорта bot.main (чтобы избежать дублирования)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)


def run_web():
    """Запуск веб-сервера в отдельном потоке."""
    import uvicorn
    from web.config import WEB_HOST, WEB_PORT
    logger.info(f"Запуск веб-сервера на {WEB_HOST}:{WEB_PORT}")
    uvicorn.run(
        "web.main:app",
        host=WEB_HOST,
        port=WEB_PORT,
        log_level="info",
    )


async def run_bot():
    """Запуск Telegram бота."""
    from bot.main import main as bot_main
    await bot_main()


def main():
    """Запуск бота и веб-сервера параллельно."""
    logger.info("Запуск бота и веб-сервера...")

    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    # Запускаем бота в главном event loop
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Остановка...")
        sys.exit(0)


if __name__ == "__main__":
    main()
