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


async def get_current_week(session: aiohttp.ClientSession) -> None:
    while True:
        try:
            async with session.get(PROXY_LINK, params={'url': SITE_LINK}, timeout=aiohttp.ClientTimeout(total=10)) as response:
                data = await response.text()


        except Exception as e:
            logger.warning("Problem with current week monitoring...", e)
            await asyncio.sleep(100)
