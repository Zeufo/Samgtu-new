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
from sqlalchemy.ext.asyncio import AsyncSession
from config import PROXY_LINK, SITE_LINK
from loguru import logger
from config import WeekState
import bs4
from services import ScheduleService 



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



async def changes_monitoring(http_session: aiohttp.ClientSession, session: AsyncSession) -> None:
    local_week = int(str(week))
    is_next_week = False

    while True:
        try:
            lc_gl_week = int(str(week))

            await cur.execute("SELECT group_id FROM schedules WHERE week_num = ?", (local_week,))
            rows = await cur.fetchall()
        
            if rows:
                for row in rows:
                    schd = await get_schedule(row[0], local_week, session, is_next_week)
                    

                    if isinstance(schd, dict):
                        schd = [schd]

                    else:
                        if isinstance(schd[0], list):
                            schd = schd[0]

                    schd = json.dumps(schd, ensure_ascii=False)#already string 

                    now = datetime.now(TZ_SAMARA)
                    await cur.execute("UPDATE schedules SET(schedule_json, last_updated_user) = (?, ?) WHERE group_id = ? AND week_num = ?", (schd, now.strftime('%d %B %H:%M'), row[0], local_week))
                    await asyncio.sleep(10)

            if local_week == lc_gl_week:
                local_week = local_week + 1
                is_next_week = True
            else:
                local_week = lc_gl_week
                is_next_week = False
            
            await db_conn.commit()
            await asyncio.sleep(1800)#1800
        except Exception as e:
            await asyncio.sleep(60)#60
            traceback.print_exc()

        await asyncio.sleep(10)
