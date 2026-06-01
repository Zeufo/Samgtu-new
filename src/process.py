from database import PostgreConnect, PostgreDBTablesCreation, PostgreFillTablesCreation
from parse import HTTPGroupParser, HTTPFacultyParser
import aiohttp
from config import SITE_LINK, ALL_GROUPS_LINK
from loguru import logger


#--------------from main-------------

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from handlers import get_main_router
#--------------------------------------
#TO WHERE I PUT THE SESSION AIOHTTP?

class Process():
    async def preparation(self, pool, first_start=False) -> None:
        if first_start:
            async with aiohttp.ClientSession() as session:
                await PostgreDBTablesCreation.create(pool)

                faculties = await HTTPFacultyParser.parse(SITE_LINK, session)

                groups = await HTTPGroupParser.parse(ALL_GROUPS_LINK, session, faculties)
                logger.info(f'groups is {groups}')
                await PostgreFillTablesCreation.fill(pool, groups) 




    def main_process(self) -> None:
        pass
