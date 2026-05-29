from os import stat
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
#from legacy.db_parcer import faculties_to_db


class Parser(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    async def parse(*args, **kwargs) -> typing.Any:
        pass





def faculties_formatter(raw) -> list:

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
    




async def parse_groups_formatter():
    groups_info = []
    
    async def add_groups_to_info(groups_from_faculty: list, course: int, faculty: int,  need_return=False):
        nonlocal groups_info 
        
        if need_return == True:
            return groups_info

        for group in groups_from_faculty:


            group['Name'] = group['Name'].rsplit(None, 1)[-1]
            group['Name'] = group['Name'].replace("–", "")
            group['Name'] = group['Name'][2:].upper()

            if len(group["Name"]) < 5 or len(group["Name"].translate(str.maketrans('', '', '1234567890'))) < 2:
                del group
                continue
            
            if group['Name'] is None:
                continue

            group['course'] = course
            #groups is list of dicts

            del group['Sort']

            to_insert = [group['ID'], group["Name"], faculty, group["course"]]

            groups_info.append(to_insert)


    return add_groups_to_info



@typing.final
class HTTPFacultyParser(Parser):
    @staticmethod
    async def parse(link, session) -> list:
        while True:
            try:
                async with session.get(link) as response:
                    raw = await response.text()#is it awaitable?ignore
                
                    return faculties_formatter(raw)

            except Exception as e:
                logger.exception(f'Unexpected error in parsing faculties...', e)
                time.sleep(1)




@typing.final
class HTTPGroupParser(Parser):
    @staticmethod
    async def parse(link, session, faculties_id: list) -> list:
        collect_groups = await parse_groups_formatter()

        for faculty in faculties_id:
            logger.info(f"parsing for {faculty} ")
            for course in range(1, 7):
                try:    
                    formated_link = link.format(course=f'{course}', faculty=f'{faculty}')
                    #formated_link = "https://samgtu.ru/students/getgrouplist?Course=4&Faculty=100111"

                    logger.info(f"link is  {formated_link} ")#efjigbnjisedfhgjidfhgjkohsdfpojgusdfpjghijsdfhgdfsg


                    async with session.get(formated_link) as response:
                        data = await response.json(content_type=None)
                        await collect_groups(data, course, faculty)

                    time.sleep(0.2) 


                except Exception as e:
                    logger.exception(f'Unexpected error in parsing faculties... Trying another', e)
                    continue

        total = await collect_groups([], 0, 0, True)
        del collect_groups

        return total#type: ignore 
        #IT cant be None because we call the func above. so no matter what we always have [] even if there were zero groups







#FINALY! we have error if not follow inheritence rules
#@typing.final
#class HTTPParser(Parser):
#    async def parse_groups(self, link, session, faculties_id: list) -> typing.List:
#        collect_groups = await parse_groups_formatter()
#
#        for faculty in faculties_id:
#            logger.info(f"parsing for {faculty} ")
#            for course in range(1,7):
#                try:    
#                    formated_link = link.format(course=f'{course}', faculty=f'{faculty}')
#                    logger.info(f"link is  {formated_link} ")#efjigbnjisedfhgjidfhgjkohsdfpojgusdfpjghijsdfhgdfsg
#
#
#                    async with session.get(formated_link) as response:
#                        data = await response.json(content_type=None)
#                        await collect_groups(data, course)
#
#                    time.sleep(0.2) 
#        
#
#
#                except Exception as e:
#                    logger.exception(f'Unexpected error in parsing faculties... Trying another', e)
#                    continue
#
#        total = await collect_groups([], 0, True)
#        del collect_groups
#        return total#type: ignore 
#       #IT cant be None because we call the func above. so no matter what we always have [] even if there were zero groups











                    





