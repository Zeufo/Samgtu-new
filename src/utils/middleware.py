from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, message
from cachetools import TTLCache


class AlchemyMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __call__(self, handler, event, data):
        async with self.session_factory() as session:
            data["session"] = session
            return await handler(event, data)


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, time_limit: int = 2):
        self.cache = TTLCache(maxsize=1000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        if isinstance(event, Update):
            inner = (
                event.message or event.edited_message or event.callback_query or event.inline_query
            )
        else:
            inner = event

        user = getattr(inner, "from_user", None) if inner else None
        if not user:
            return await handler(event, data)

        user_id = user.id

        if user_id in self.cache:
            return

        self.cache[user_id] = True
        return await handler(event, data)
