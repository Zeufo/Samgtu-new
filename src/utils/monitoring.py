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
from config import PROXY_LINK, SITE_LINK
from loguru import logger
from config import WeekState
import bs4


async def get_current_week(session: aiohttp.ClientSession) -> None:
    while True:
        try:
            async with session.get(PROXY_LINK, params={'url': SITE_LINK}, timeout=aiohttp.ClientTimeout(total=10)) as response:
                data = await response.text()

                find_week = bs4.BeautifulSoup(data, 'html.parser')
                find_week = find_week.find('select', id = 'schedule_weekttype_select').find('option', selected=True)#type: ignore
                WeekState.week = find_week['value']#type: ignore

                await asyncio.sleep(3600)


        except Exception as e:
            logger.warning("Problem with current week monitoring...", e)
            await asyncio.sleep(100)
