from database import PostgresConnect, PostgresDBTablesCreation
from parse import HTTPParser
import aiohttp
from config import SITE_LINK, ALL_GROUPS_LINK


#TO WHERE I PUT THE SESSION AIOHTTP?

class Process():
    #def __init__(self, pool) -> None:
        #connection = PostgresConnect()
        #self.pool = pool #connection.get_pool()

    async def preparation(self, pool, first_start=False) -> None:
        async with aiohttp.ClientSession() as session:
            Parser = HTTPParser()
            await PostgresDBTablesCreation.create(pool)

            if first_start:
                faculties = Parser.parse_faculties(SITE_LINK, session)
                groups = Parser.parse_groups(ALL_GROUPS_LINK, session, faculties)
                print(groups)
           
            



    def main_process(self) -> None:
        pass
