import asyncio
from aiogram.types import Message
import aiohttp
from loguru import logger
import re

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types


from pydantic_core.core_schema import to_string_ser_schema
from sqlalchemy import JSON, select, true, update, delete, and_
from sqlalchemy.dialects.postgresql import insert

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import orm_insert_sentinel
from database import User, Group
from database.models import AsyncSessionLocal

from database.models import Schedule, User
from config import WeekState
from services.registration_service import UserService, GroupService
from parse import HTTPScheduleParser
import aiohttp
from config import WeekState

import time
import json
import re
import datetime

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import locale
import typing
import locale



TZ_SAMARA = ZoneInfo('Europe/Samara')
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')





class ScheduleService():
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_schedule(self, week:int, group:int) -> list[typing.Any] | None:
        query = select(Schedule.schedule_json).where(and_(Schedule.group_id==group, Schedule.week_num==week))
        result = await self.session.execute(query) 

        return result.scalar_one_or_none()


    #to_insert = (group_id, WeekState.week, schd, "Not now", time_now_seconds, time_now.strftime('%d %B %H:%M'))#type:ignore
    async def insert_schedule(self, session: AsyncSession, to_insert: tuple) -> None:
        stmt =  insert(Schedule).values(group_id=to_insert[0], week_num=to_insert[1], schedule_json=to_insert[2], to_compare=to_insert[3], last_updated=to_insert[4], last_updated_formated=to_insert[5])
        await session.execute(stmt)
        await session.commit()


#we use this to get normal keys from database. actually im not sure if we really need that, but legacy code didnt worked without it
#so let is just be 
async def output_formatter(raw) -> list | dict | None:
    if isinstance(raw, list):
        for day in raw:
            old_lst = day['lessons']
            day['lessons'] = {int(key): value for key, value in old_lst.items()}
        return raw


    if isinstance(raw, dict):
        old_lst = raw.get('lessons', {})
        raw['lessons'] = {int(key): value for key, value in old_lst.items() if str(key).isdigit()}
        return raw
    

icons = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
#wee need to activate parse_mode='HTML' in message.answer
#I DONT UNDERTSTAND WHY WE USE CHECK TO IF LN < 2? SO I COMMENT It, MAybe one day well nedd thath
async def message_maker(raw: list | dict) -> str:
    #print(f'schd is... \n{sА почему chd}\n\n\n')

    temp_msg = ''
    temp_msg = ''
    

    if isinstance(raw, dict):
        raw = [raw]

    if isinstance(raw[0], list):
        raw = raw[0]


    for day in  raw:
        ln = len(day['lessons'])
        logger.info(f'day is {day}')


        if ln < 2 and day['lessons'].get(1, {}).get('пара', 0) != 'Выходной': 
            continue



        temp_msg += f'📅<b>{day['day_name']}</b>, '
        temp_msg += f'{day['week_day']}\n'
       


        for lesson in range(1, ln + 1):
            temp_msg += f'\n{icons[lesson-1]}\u200b<b><code>{day["lessons"][lesson]["время"]}</code></b>\n'
            #temp_msg += f'\n{icons[lesson-1]}<b><code>{day['lessons'][lesson]['время']}</code></b>\n'
            ls_type = re.search(r'\((.*?)\)',  day['lessons'][lesson]['пара'])
            emoji ='📚'

            if ls_type:
                ls_type_found = ls_type.group(1)

                match ls_type_found:
                    case 'лекция': emoji ='📚'
                    case 'практика': emoji = '✏️'
                    case 'лаба': emoji ='🔬'

                     

            parts = day['lessons'][lesson]['пара'].split('ауд.')
            

            ln = len(parts)
            if ln < 2:
                parts.append('\tне указана')
            temp_msg += f"{emoji}{parts[0].strip()}\n📍ауд.{parts[1]}\n"
        
        temp_msg += '\n'
        temp_msg += '_________________________________\n\n'

    return temp_msg 



async def date_setter(no_date_schedule: list, is_next: bool) ->  None:
    today = datetime.now(TZ_SAMARA)
    start_of_week = today - timedelta(days=today.weekday())

    if is_next:
        start_of_week += timedelta(days=7)

    i = 0
    for cell in no_date_schedule:

        day = (start_of_week + timedelta(days=i))    
        logger.info(f"day in date setter is... {day}")#---------------------------------
        cell['week_day'] = day.strftime('%d %B')
        i = i + 1





#FIX how data is showed. should make cleaner forget that it works with tume and make it do in this func instead
async def schedule_week_service(message: Message, session: AsyncSession, http_session: aiohttp.ClientSession, is_next_week=False) -> list | dict | None:
    try:
        UserServ = UserService(session)

        group_id = await UserServ.get_user_group(message.chat.id) 
        
        logger.info(f'Group id is \n\n\n\n{group_id}\n\n\n\n')
        if group_id is None:
            return None

        ScheduleServ = ScheduleService(session)
        GroupServ = GroupService(session)

        week = WeekState.week
        time_now = datetime.now(TZ_SAMARA)

        if is_next_week == True:
            week = WeekState.week + 1


        schd = await output_formatter(await ScheduleServ.get_schedule(week, group_id))
        
        if schd is None:
            logger.info(f'trying to parse with week {week} amd group {group_id}')
            schd = await HTTPScheduleParser.parse(http_session, group_id, week)
            await date_setter(schd, is_next_week)



            time_now_seconds = int(time_now.timestamp())
            to_insert = (group_id, week, schd, "Not now", time_now_seconds, time_now.strftime('%d %B %H:%M'))#type:ignore
            logger.info(f"to insert is... \n\n{to_insert}\n\n")#--------------------------------------------------------------------


            await ScheduleServ.insert_schedule(session, to_insert)
            logger.info('New schedule was added')#--------------------------------------------------------------------------------------

        #msg = await message_maker(schd)#type:ignore  it cant be none since we parcing
        return schd

    except Exception as e:
        logger.exception('Problem with sending schedule service...', e)


days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
async def schedule_day_service(message: Message, session: AsyncSession, http_session: aiohttp.ClientSession, is_next_day=False) -> list | None | str:
    try:
        logger.info("Started the schedule service")#---------------------------------------------------------------------------

        time_now = datetime.now(TZ_SAMARA)

        if is_next_day:
            time_now += timedelta(days=1)


        if time_now.weekday() == 0:
            schd = await schedule_week_service(message, session, http_session, True) 

        else:
            schd = await schedule_week_service(message, session, http_session) 



        if schd is None:
            logger.info("Schd is None... returning the list now")#---------------------------------------------------------------------------
            return 'Выходной'

        for day in schd:
            if days[time_now.weekday()] in day.values():
                if len(day.get('lessons', 0)) == 0:
                    #'lessons': {1: {'пара': 'Физика (лекция)  ауд. 104 корпус №10', 'время': '8:00-9:35'}
                    day['lessons'] = {1: {'пара': 'Выходной', 'время': 'Отсутствует'}}
                    logger.info("len of day is none... returning the list now")#---------------------------------------------------------------------------
                    return [day]
                else:
                    return[day]
            



    except Exception as e:
        logger.exception('Problem with sending schedule service...', e)




async def schedule_next_day_service(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pass




