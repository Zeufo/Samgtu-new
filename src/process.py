from database import PostgreConnect, PostgreDBTablesCreation, PostgreFillTablesCreation
from parse import HTTPGroupParser, HTTPFacultyParser
import aiohttp
from config import SITE_LINK, ALL_GROUPS_LINK
from loguru import logger

#TO WHERE I PUT THE SESSION AIOHTTP?

class Process():
    async def preparation(self, pool, first_start=False) -> None:
        async with aiohttp.ClientSession() as session:
            await PostgreDBTablesCreation.create(pool)

            if first_start:
                faculties = await HTTPFacultyParser.parse(SITE_LINK, session)

                groups = await HTTPGroupParser.parse(ALL_GROUPS_LINK, session, faculties)
                logger.info(f'groups is {groups}')
                await PostgreFillTablesCreation.fill(pool, groups) 




    def main_process(self) -> None:
        pass
