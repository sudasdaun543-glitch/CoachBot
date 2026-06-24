from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.config import ADMIN_IDS


class AdminMiddleware(BaseMiddleware):
    """Middleware, который проверяет, является ли пользователь админом."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id
            data["is_admin"] = user_id in ADMIN_IDS
        return await handler(event, data)
