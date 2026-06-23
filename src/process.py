import asyncio

import aiohttp
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import (
    AsyncSessionLocal,
    PostgreDBTablesCreation,
    PostgreFillTablesCreation,
)
from handlers import get_main_router
from parse import HTTPFacultyParser, HTTPGroupParser
from utils import AlchemyMiddleware, AntiSpamMiddleware, changes_monitoring, logger


class ProgrammProcess:
    async def preparation(self, first_start=True) -> None:
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
        dp.update.outer_middleware(AntiSpamMiddleware(1))

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
                task1.cancel()  # type:ignore
                task2.cancel()  # type:ignore

                await asyncio.gather(task1, task2, return_exceptions=True)  # type:ignore
                logger.info("Tasks are closed")
