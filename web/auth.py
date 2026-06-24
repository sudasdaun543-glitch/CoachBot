"""
Telegram Login Widget авторизация.

Документация: https://core.telegram.org/widgets/login
"""

import hashlib
import hmac
import json
from typing import Any

from web.config import TELEGRAM_BOT_TOKEN


def verify_telegram_login(data: dict[str, Any]) -> bool:
    """
    Проверяет подпись данных от Telegram Login Widget.

    Алгоритм:
    1. Берём все поля кроме 'hash'
    2. Сортируем по имени поля
    3. Формируем строку key=value\\n...
    4. Создаём HMAC-SHA256 с токеном бота как ключом
    5. Сравниваем с переданным hash
    """
    received_hash = data.pop("hash", "")
    if not received_hash:
        return False

    # Сортируем поля по алфавиту
    sorted_items = sorted(data.items(), key=lambda x: x[0])
    check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)

    # Создаём HMAC-SHA256
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(
        secret_key, check_string.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_hash, received_hash)
