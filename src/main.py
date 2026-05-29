#from loguru import logger
#import sys
from process import Process
from database import PostgreConnect
import asyncio
from utils.logger import logger
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()


    logger.info("Main started!")
    pool = await PostgreConnect.get_async_pool()
    MainProcess = Process()
    await MainProcess.preparation(pool, True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass

