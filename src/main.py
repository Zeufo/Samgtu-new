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
from utils import changes_monitoring
import locale





locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


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
           
        try:
            task1 = asyncio.create_task(dp.start_polling(bot))
            task2 = asyncio.create_task(changes_monitoring(httpsession, AsyncSessionLocal))
            await asyncio.gather(task1, task2)

        except asyncio.CancelledError:
            logger.info("Stop signal recived")
            raise

        finally:
            task1.cancel()#type:ignore
            task2.cancel()#type:ignore

            await asyncio.gather(task1,task2, return_exceptions=True)#type:ignore
            logger.info('Tasks are closed')



if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass

