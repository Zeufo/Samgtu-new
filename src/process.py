from database import PostgreConnect, PostgreDBTablesCreation, PostgreFillTablesCreation
from parse import HTTPGroupParser, HTTPFacultyParser
import aiohttp
from config import SITE_LINK, ALL_GROUPS_LINK
from loguru import logger
from database import AsyncSessionLocal



#from loguru import logger
#import sys
from aiohttp.http import HttpRequestParser
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





class ProgrammProcess():
    async def preparation(self, first_start=False) -> None:
        await PostgreDBTablesCreation.create()

        if first_start:
            async with aiohttp.ClientSession() as session:
                faculties = await HTTPFacultyParser.parse(session)

                groups = await HTTPGroupParser.parse(session, faculties)
                await PostgreFillTablesCreation.fill(groups) 



    async def main_process(self) -> None:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()

        logger.info("Process started!")

        PreparationProcess = ProgrammProcess()
        await PreparationProcess.preparation(False)
        logger.info("Preparation passed")
        
        dp.include_router(get_main_router())
        dp.update.middleware(AlchemyMiddleware(session_factory=AsyncSessionLocal))

        logger.info("Starting bot...")


        async with aiohttp.ClientSession() as httpsession:
            dp["http_session"] = httpsession
            
            try:
                task1 = asyncio.create_task(dp.start_polling(bot))
                task2 = asyncio.create_task(changes_monitoring(httpsession, AsyncSessionLocal, bot))
                await asyncio.gather(task1, task2)

            except asyncio.CancelledError:
                logger.info("Stop signal recived")
                raise

            finally:
                task1.cancel()#type:ignore
                task2.cancel()#type:ignore

                await asyncio.gather(task1,task2, return_exceptions=True)#type:ignore
                logger.info('Tasks are closed')

