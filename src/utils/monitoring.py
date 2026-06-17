import asyncio
import hashlib
import json
import locale
import os
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Optional
from weakref import ProxyType
from zoneinfo import ZoneInfo

import aiogram
import aiohttp
import bs4
from loguru import logger
from psycopg.errors import SchemaAndDataStatementMixingNotSupported
from sqlalchemy.ext.asyncio import AsyncSession

from config import PROXY_LINK, SITE_LINK, TZ_SAMARA, WeekState
from parse import HTTPScheduleParser, datacleaner
from services import NotifyUsers, ScheduleService, date_setter


async def week_changes_monitoring(http_session: aiohttp.ClientSession) -> None:
    while True:
        try:
            async with http_session.get(
                PROXY_LINK,
                params={"url": SITE_LINK},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                data = await response.text()

                find_week = bs4.BeautifulSoup(data, "html.parser")
                find_week = find_week.find(
                    "select", id="schedule_weekttype_select"
                ).find("option", selected=True)  # type: ignore
                WeekState.week = int(find_week["value"])  # type: ignore
                await asyncio.sleep(3600)

        except Exception as e:
            logger.warning("Problem with week monitoring...", e)
            await asyncio.sleep(100)


def schedule_hash(schedule: list) -> str:
    raw = json.dumps(schedule, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


async def schedule_diff_seeker(old: list, new: list) -> list:
    changes = []

    old_by_day = {day["day_name"]: day["lessons"] for day in old}
    new_by_day = {day["day_name"]: day["lessons"] for day in new}

    for day_name, new_lessons in new_by_day.items():
        old_lessons = old_by_day.get(day_name, {})

        all_pair_numbers = set(old_lessons) | set(new_lessons)

        for pair_num in sorted(all_pair_numbers):
            old_lesson = old_lessons.get(pair_num)
            new_lesson = new_lessons.get(pair_num)

            if old_lesson is None and new_lesson is not None:
                changes.append(
                    f"➕ {day_name}, пара {pair_num}: добавлено "
                    f"«{new_lesson['пара']}» ({new_lesson['время']})"
                )
            elif old_lesson is not None and new_lesson is None:
                changes.append(
                    f"➖ {day_name}, пара {pair_num}: убрано "
                    f"«{old_lesson['пара']}» ({old_lesson['время']})"
                )
            elif old_lesson != new_lesson:
                changes.append(
                    f"✏️ {day_name}, пара {pair_num}: было "
                    f"«{old_lesson['пара']}» ({old_lesson['время']}), "
                    f"стало «{new_lesson['пара']}» ({new_lesson['время']})"
                )

    return changes


async def changes_monitoring(
    http_session: aiohttp.ClientSession, session_maker, bot: aiogram.Bot
) -> None:
    await asyncio.sleep(10)
    while True:
        notify_users = NotifyUsers(bot)
        local_week = int(WeekState.week)
        async with session_maker() as session:
            schedule_serv = ScheduleService(session)
            week: int = WeekState.week

            try:
                week: int = WeekState.week
                time_now = datetime.now(TZ_SAMARA)

                rows = await schedule_serv.get_groups_id(week)  # [(id1, id2, id3)]
                logger.debug(f"rows is... {rows}")

                if rows:
                    for row in rows[0]:  # row here is group id
                        new_schd = await HTTPScheduleParser.parse(
                            http_session, row, local_week
                        )
                        await date_setter(new_schd, False, time_now)
                        new_hash = schedule_hash(new_schd)

                        data = await schedule_serv.get_schedule_and_hash(
                            week, row
                        )  # [( [{}], 'str')]
                        old_schd = data[0][0]  # type:ignore
                        old_hash = data[0][1]  # type:ignore

                        if old_schd is None or old_hash is None:
                            logger.info(
                                f"Schedule is None for  {row} at {week}... why?"
                            )
                            continue

                        if new_hash == old_hash:
                            update = {
                                "last_updated_formated": time_now.strftime(
                                    "%d %B %H:%M"
                                )
                            }
                            await schedule_serv.update_schedule_for_monitoring(
                                row, update
                            )
                            return

                        else:
                            logger.info(f"Schedule changed for {row}... starting alarm")
                            changes = await schedule_diff_seeker(old_schd, new_schd)
                            await notify_users.send()

                        return

                        await cur.execute(
                            "UPDATE schedules SET(schedule_json, last_updated_user) = (?, ?) WHERE group_id = ? AND week_num = ?",
                            (schd, now.strftime("%d %B %H:%M"), row[0], local_week),
                        )
                        await asyncio.sleep(10)

                if local_week == lc_gl_week:
                    local_week = local_week + 1
                    is_next_week = True
                else:
                    local_week = lc_gl_week
                    is_next_week = False

                # await db_conn.commit()
                # await asyncio.sleep(1800)#1800
            except asyncio.CancelledError:
                raise

            except Exception as e:
                await asyncio.sleep(60)  # 60

        await asyncio.sleep(10)
