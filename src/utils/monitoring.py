import asyncio
import re
import time
import sys
import os
from datetime import datetime, timedelta
from weakref import ProxyType
from zoneinfo import ZoneInfo
import locale
from typing import Optional
import aiohttp
from psycopg.errors import SchemaAndDataStatementMixingNotSupported
from sqlalchemy.ext.asyncio import AsyncSession

from loguru import logger
import bs4
from services import ScheduleService 
from config import WeekState
from config import PROXY_LINK, SITE_LINK
import json
from config import TZ_SAMARA

import hashlib




async def week_changes_monitoring(http_session: aiohttp.ClientSession) -> None:
    while True:
        try:
            async with http_session.get(PROXY_LINK, params={'url': SITE_LINK}, timeout=aiohttp.ClientTimeout(total=10)) as response:
                data = await response.text()

                find_week = bs4.BeautifulSoup(data, 'html.parser')
                find_week = find_week.find('select', id = 'schedule_weekttype_select').find('option', selected=True)#type: ignore
                WeekState.week = int(find_week['value'])#type: ignore
                await asyncio.sleep(3600)


        except Exception as e:
            logger.warning("Problem with week monitoring...", e)
            await asyncio.sleep(100)




def schedule_hash(schedule: list) -> str:
    raw = json.dumps(schedule, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


async def changes_monitoring(http_session: aiohttp.ClientSession, session_maker) -> None:
    await asyncio.sleep(10)

    local_week = int(WeekState.week)
    is_next_week = False
    async with session_maker() as session:

        ScheduleServ = ScheduleService(session)
        week = WeekState.week

        while True:
            try:
                week = WeekState.week
                week:int 
                lc_gl_week = int(str(week))

                rows = await ScheduleServ.get_groups_id(week)#[(id1, id2, id3)]

                logger.debug(f'rows is... {rows}')
            
                if rows:
                    for row in rows[0]:#row here is group id
                        data = await ScheduleServ.get_schedule_and_hash(week, row)# [( [{}], 'str')]
                        schd = data[0][0]#type:ignore
                        hash = data[0][1]#type:ignore

                        if schd is None or hash is None:
                            logger.warning(f'SCHEDULE IS NONE FOR {row} AT {week}... WHY?\t with schd {schd}\n\n and{hash}')
                            continue
                                
                        now = datetime.now(TZ_SAMARA)

                        new_hash = schedule_hash(schd)
                        if new_hash == hash:
                            update = {'last_updated_formated': now.strftime('%d %B %H:%M')}
                            await ScheduleServ.update_schedule_for_monitoring(row, update)
                            return

                        else:
                            logger.critical("justt cheking if hash working now. no need for panic")

                        return 


                        await cur.execute("UPDATE schedules SET(schedule_json, last_updated_user) = (?, ?) WHERE group_id = ? AND week_num = ?", (schd, now.strftime('%d %B %H:%M'), row[0], local_week))
                        await asyncio.sleep(10)

                if local_week == lc_gl_week:
                    local_week = local_week + 1
                    is_next_week = True
                else:
                    local_week = lc_gl_week
                    is_next_week = False
                
                #await db_conn.commit()
                #await asyncio.sleep(1800)#1800
            except asyncio.CancelledError:
                raise

            except Exception as e:
                await asyncio.sleep(60)#60

            await asyncio.sleep(10)
