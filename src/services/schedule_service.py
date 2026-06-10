import asyncio
from aiogram.types import Message
import aiohttp
from loguru import logger
import re

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types


from sqlalchemy import select, update, delete, and_
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


TZ_SAMARA = ZoneInfo('Europe/Samara')



class ScheduleService():
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_schedule(self, week:int, group:int) -> str | None:
        query = select(Schedule.schedule_json).where(and_(Schedule.group_id==group, Schedule.week_num==week))
        result = await self.session.execute(query) 

        return result.scalar_one_or_none()

    async def insert_schedule(self, session: AsyncSession, to_insert: tuple) -> None:
        stmt =  insert(Schedule).values(to_insert)
        await session.execute(stmt)
        await session.commit()


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
async def message_maker(raw: list | dict) -> str:
    #print(f'schd is... \n{sА почему chd}\n\n\n')

    temp_msg = ''
    temp_msg = ''
    
    if isinstance(raw, dict):
        raw = [raw]

    for day in  raw:
        ln = len(day['lessons'])

        temp_msg += f'📅<b>{day['day_name']}</b>, '
        temp_msg += f'{day['week_day'][0]}\n'
       

        for lesson in range(1, ln + 1):
            temp_msg += f'\n{icons[lesson-1]}<b><code>{day['lessons'][lesson]['время']}</code></b>\n'
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




async def schedule_this_week_service(message: Message, session: AsyncSession, http_session: aiohttp.ClientSession) -> None:
    try:
        UserServ = UserService(session)
        ScheduleServ = ScheduleService(session)
        GroupServ = GroupService(session)

        group_id = await UserServ.get_user_group(message.chat.id) 

        if group_id is None:
            await message.answer("Пожалуйста, пройдите регистрацию/n/start")
            return


        msg = await output_formatter(await ScheduleServ.get_schedule(WeekState.week, group_id))
        
        if msg is None:
            logger.info(f'trying to parse with week {WeekState.week} amd group {group_id}')
            msg = await HTTPScheduleParser.parse(http_session, group_id, WeekState.week)
            schd = msg[0] 
            #no_date_schd = msg[1]


            time_now = datetime.now(TZ_SAMARA)
            time_now_seconds = int(time_now.timestamp())

            to_insert = (group_id, WeekState.week, schd, "Not now", time_now_seconds, time_now)#type:ignore

            await ScheduleServ.insert_schedule(session, to_insert)
            logger.info('New schedule was added')


        msg = await message_maker(msg)#type:ignore  it cant be none since we parcing
        await message.answer(msg, parse_mode='HTML')
        logger.info("giving schedule to the user...")

    except Exception as e:
        logger.exception('Problem with sending schedule service...', e)


async def schedule_next_week_service(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pass

async def schedule_this_day_service(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pass

async def schedule_next_day_service(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pass




