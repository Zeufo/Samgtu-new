#from loguru import logger
#import sys
from process import Process
from database import PostgreConnect
import asyncio
from utils.logger import logger
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from handlers import get_main_router
from database.models import AsyncSessionLocal
from database import AlchemyMiddleware, AsyncpgMiddleware

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    logger.info("Main started!")

    pool = await PostgreConnect.get_async_pool()
    PreparationProcess = Process()
    await PreparationProcess.preparation(pool, False)

    dp.include_router(get_main_router())
    dp.update.middleware(AlchemyMiddleware(session_factory=AsyncSessionLocal))
    dp.update.middleware(AsyncpgMiddleware(pool))

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass

