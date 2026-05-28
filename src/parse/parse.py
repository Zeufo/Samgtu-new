import requests
import aiohttp
import abc
import typing
import asyncio
import aiohttp
import requests
import bs4
from loguru import logger
import time 
from config import GroupsDictValues
from legacy.db_parcer import faculties_to_db


class Parser(abc.ABC):
    async def parse(self, link, session) -> typing.Any:
        pass


class Cleaner(abc.ABC):
    async def clean(self, obj: typing.Any) -> typing.Any:
        pass



def faculties_formatter(raw: str) -> list:

    soup = bs4.BeautifulSoup(raw, "lxml")
    faculties = soup.find("select", class_="schedule-selects")

    if faculties:
        faculties = faculties.find_all("option")
    
        faculties_id = []
        for i in faculties:
            key = i.get("value")#Тут разворачиваем где value=""

            if key == "":
                continue

            faculties_id.append(key)#all faculties keys

        return faculties_id

    else:
        raise RuntimeError
    



def parse_groups_formatter():
    groups_info = []
    
    def add_groups_to_info(groups_from_faculty: list, course: int, need_return=False):
        nonlocal groups_info 
        
        if need_return == True:
            return groups_info

        for group in groups_from_faculty:


            group['name'] = group['name'].rsplit(None, 1)[-1]
            group['name'] = group['name'].replace("–", "")
            group['name'] = group['name'][2:].upper()
            group['course'] = course
            #groups is list of dicts 
            del group['Sort']

        groups_info.append(groups_from_faculty)

    return add_groups_to_info




class HTTPParser(Parser):
    async def parse_faculties(self, link, session) -> typing.Any:#link is the site link
        try:
            async with session.get(link) as response:
                raw = response.text#is it awaitable?
                return faculties_formatter(raw)

        except Exception as e:
            logger.exception(f'Unexpected error in parsing faculties...', e=e)
            raise RuntimeError 



    async def parse_groups(self, link, session, faculties_id) -> typing.List:
        collect_groups = parse_groups_formatter()

        for faculty in faculties_id:
            for course in range(1,7):
                try:    
                    link.format(course=f'{course}', faculty=f'{faculty}')


                    async with session.get(link) as response:
                        collect_groups(response.json(), course)
                    time.sleep(0.2) 
        


                except Exception as e:
                    logger.exception(f'Unexpected error in parsing faculties... Trying another', e=e)
                    continue

        total = collect_groups([], 0, True)
        del collect_groups
        return total#type: ignore 
        #IT cant be None because we call the func above. so no matter what we always have [] even if there were zero groups











                    





