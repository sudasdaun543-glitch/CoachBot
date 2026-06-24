"""
Скрипт для запуска и бота, и веб-сервера одновременно.
Используется на Railway (один сервис для всего).
"""
import asyncio
import logging
import os
import sys

# Настраиваем логгирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_bot():
    """Запуск Telegram бота."""
    from bot.main import main as bot_main
    await bot_main()


async def run_web():
    """Запуск веб-сервера."""
    import uvicorn
    from web.config import WEB_HOST, WEB_PORT
    logger.info(f"Запуск веб-сервера на {WEB_HOST}:{WEB_PORT}")
    config = uvicorn.Config(
        "web.main:app",
        host=WEB_HOST,
        port=WEB_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Запуск бота и веб-сервера параллельно."""
    logger.info("Запуск бота и веб-сервера...")
    await asyncio.gather(
        run_bot(),
        run_web(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка...")
        sys.exit(0)
