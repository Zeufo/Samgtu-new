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
import json


from sqlalchemy.ext.asyncio import AsyncSession 
from config import SITE_LINK, GroupsDictValues
#from legacy.db_parcer import faculties_to_db
from config import SCHD_LINK, ALL_GROUPS_LINK

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
    async def parse(session) -> list:
        while True:
            try:
                async with session.get(SITE_LINK) as response:
                    raw = await response.text()#is it awaitable?ignore
                
                    return faculties_formatter(raw)

            except Exception as e:
                logger.exception(f'Unexpected error in parsing faculties...', e)
                time.sleep(1)


@typing.final
class HTTPGroupParser(Parser):
    @staticmethod
    async def parse(session: aiohttp.ClientSession, faculties_id: list) -> list:
        collect_groups = await parse_groups_formatter()

        for faculty in faculties_id:
            logger.info(f"parsing for {faculty} ")
            for course in range(1, 7):
                try:    
                    formated_link = ALL_GROUPS_LINK.format(course=f'{course}', faculty=f'{faculty}')
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



@typing.final
class HTTPScheduleParser(Parser):
    @staticmethod
    async def parse(session: aiohttp.ClientSession, grp_id: str, weeknum: int) -> None:
        formated_link = SCHD_LINK.format(course=f'{grp_id}',  weeknumber=f'{weeknum}')
        timeout = aiohttp.ClientTimeout(total=10)

        async with session.get(formated_link, timeout=timeout) as response:
            pass



#Okay< here the funadmental func. it will request every 30 min schedule to the group from db 
#so we need put in func week, grp_id or maybe take it from the data base
#this func will work every 30 min or when user asks.
async def clean_schedule(response):
        raw_text = await response.text()

        try:
            json_start = raw_text.find('{')
            if json_start != -1:
                clean_json_str = raw_text[json_start:]
                data = json.loads(clean_json_str)
            else:
                return {}

        except json.JSONDecodeError as e:
            return {}

        cleanr = re.compile('<.*?>')

        def clean_text(text):
            if not text: return ""
            text = re.sub(cleanr, ' ', text)
            text = text.replace('^', '')
            text = text.replace('\xa0', ' ').strip()
            return text
        
        days = data.get('wd', {})
       
        schedule = []
        no_date_schedule = []

        no_date_temp = {}
        temp = {}

        #day_id = 0

        i = 0
       
        today = datetime.now(TZ_SAMARA)
        start_of_week = today - timedelta(days=today.weekday())


        if is_next == True:
            start_of_week = start_of_week + timedelta(days=7)

        for day_id, day_data in days.items():
            day_name = day_data.get("Name")
            times = day_data.get('at', {})
    
            temp = {'day_name': day_name}
            #lessons_info_temp = {}#-----------------------

            day = start_of_week + timedelta(days=i)        
                    #week_day = day.strftime('%A')

            date_name = day.strftime('%d %B')

            temp['week_day'] = date_name,
            temp['lessons'] = {}
            no_date_temp['lessons'] = {}       
                    

            less = 1

            for time_id, time_info in times.items():

                cells = time_info.get("Cells", [])

                if not cells:
                    continue
                

                for cell in cells:
                    time_name = clean_text(time_info.get("Name"))
                    content = clean_text(cell.get('CellName', ''))
                    week_type = cell.get("WeekTypeName", '')
                   
                    
                    if content is not None:
                        temp['lessons'][less] = {'пара' : content.replace('№ ', '№').replace('лекция', '(лекция)').replace('практические занятия','(практика)').replace('лабораторные занятия', '(лаба)').replace('аудитория', 'ауд.').replace(',',''), 'время': time_name.replace(' -', '-').replace(' ', ':')} 
                        no_date_temp['lessons'][less] = {'пара' : content.replace('№ ', '№').replace('лекция', '(лекция)').replace('практические занятия','(практика)').replace('лабораторные занятия', '(лаба)').replace('аудитория', 'ауд.').replace(',',''), 'время': time_name.replace(' -', '-').replace(' ', ':')} 
                    #lessons_info_temp[f'lesson {less}'] = content,
                    #lessons_info_temp['time'] = time_name

                    less = less + 1

            i += 1

            #temp[f'less_inf'] = lessons_info_temp

            #print(f"temp now is... {temp}")
            schedule.append(temp)
            no_date_schedule.append(no_date_temp)
        #print(f'sch to return... {schedule}')
        return [schedule, no_date_schedule]



                    





