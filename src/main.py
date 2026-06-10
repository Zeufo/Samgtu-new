#from loguru import logger
#import sys
from aiohttp.http import HttpRequestParser
from process import Process
from database import PostgreConnect
import asyncio
from utils import logger
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from handlers import get_main_router
from database import AsyncSessionLocal
from database import AlchemyMiddleware
import aiohttp

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    logger.info("Main started!")

    session = await PostgreConnect.get_alchemy_conn()
    logger.info("Got alchemy session")
    PreparationProcess = Process()
    await PreparationProcess.preparation(session, False)
    logger.info("Preparation passed")
    
    dp.include_router(get_main_router())
    dp.update.middleware(AlchemyMiddleware(session_factory=AsyncSessionLocal))

    logger.info("Starting bot...")


    async with aiohttp.ClientSession() as httpsession:
        dp["http_session"] = httpsession

        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass

