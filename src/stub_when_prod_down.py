import asyncio
import time
from typing import Any, Callable, Dict

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.types import Message, TelegramObject

# Замените на токен вашего бота
BOT_TOKEN = "TOKEN"


# Простой антиспам Middleware (ограничение по времени между сообщениями)
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 3.0):
        self.limit = limit
        self.last_time: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            now = time.time()

            # Если пользователь пишет чаще, чем раз в limit секунд — игнорируем
            if user_id in self.last_time and (now - self.last_time[user_id]) < self.limit:
                return

            self.last_time[user_id] = now

        return await handler(event, data)


dp = Dispatcher()


# Ловим вообще любое входящее сообщение (текст, команду, стикер и т.д.)
@dp.message()
async def tech_works_handler(message: Message):
    await message.answer(
        "Производятся технические работы на сервере, просим прощения за неудобства"
    )


async def main():
    bot = Bot(token=BOT_TOKEN)

    # Подключаем антиспам (срабатывает не чаще раза в 3 секунды от одного пользователя)
    dp.message.middleware(ThrottlingMiddleware(limit=3.0))

    # Сбрасываем старые накопившиеся сообщения и запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
