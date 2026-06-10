from database import PostgreConnect, PostgreDBTablesCreation, PostgreFillTablesCreation
from parse import HTTPGroupParser, HTTPFacultyParser
import aiohttp
from config import SITE_LINK, ALL_GROUPS_LINK
from loguru import logger
from database import AsyncSessionLocal


class Process():
    async def preparation(self, alch_session, first_start=False) -> None:
        async with aiohttp.ClientSession() as session:
            await PostgreDBTablesCreation.create(alch_session)


            if first_start:
                faculties = await HTTPFacultyParser.parse(session)
                groups = await HTTPGroupParser.parse(session, faculties)
                await PostgreFillTablesCreation.fill(alch_session, groups) 




    def main_process(self) -> None:
        pass
