import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Login Widget
TELEGRAM_BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
TELEGRAM_BOT_NAME: str = os.getenv("TELEGRAM_BOT_NAME", "CoachingOperatorsBot")

# Веб-сервер
# Railway автоматически задаёт PORT, используем его если есть
WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT: int = int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))
SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")

# Админы из конфига бота
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]
