import asyncio
import hashlib
import json
from datetime import datetime

import aiogram
import aiohttp
import bs4
from loguru import logger

from config import PROXY_LINK, SITE_LINK, TZ_SAMARA, WeekState
from parse import HTTPScheduleParser
from services import NotifyUsers, ScheduleService, UserService, date_setter


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
                find_week = find_week.find("select", id="schedule_weekttype_select").find(  # type:ignore
                    "option", selected=True
                )
                WeekState.week = int(find_week["value"])  # type: ignore
                await asyncio.sleep(3600)

        except Exception as e:
            logger.warning("Problem with week monitoring...", e)
            await asyncio.sleep(100)


def schedule_hash(schedule: list) -> str:
    raw = json.dumps(schedule, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


async def schedule_diff_seeker(old: list, new: list) -> str:
    logger.debug(f"old is {old}")
    changes = []

    old_by_day = {
        day["day_name"]: {
            "lessons": {int(k): v for k, v in day["lessons"].items()},
            "week_day": day["week_day"],
        }
        for day in old
    }
    new_by_day = {
        day["day_name"]: {
            "lessons": {int(k): v for k, v in day["lessons"].items()},
            "week_day": day["week_day"],
        }
        for day in new
    }

    for day_name, day_data in new_by_day.items():
        new_lessons = day_data["lessons"]
        week_day = day_data["week_day"]

        old_lessons = old_by_day.get(day_name, {}).get("lessons", {})
        all_pair_numbers = set(old_lessons) | set(new_lessons)

        for pair_num in sorted(all_pair_numbers):
            old_lesson = old_lessons.get(pair_num)
            new_lesson = new_lessons.get(pair_num)

            if old_lesson is None and new_lesson is not None:
                changes.append(
                    f"✳️ Добавили\n<b>{day_name}, {week_day}</b>, пара {pair_num}\n"
                    f"⏱️<code>{new_lesson['время']}</code>\n"
                    f"📚{new_lesson['пара'].replace('ауд.', ' | ауд.')}\n"
                )
                changes.append("_________________________________\n")
            elif old_lesson is not None and new_lesson is None:
                changes.append(
                    f"❌ убрали\n <b>{day_name}, {week_day}</b>, пара {pair_num}\n"
                    f"⏱️<code>{old_lesson['время']}</code>\n"
                    f"📚{old_lesson['пара'].replace('ауд.', ' | ауд.')}\n"
                )

                changes.append("_________________________________\n")
            elif old_lesson != new_lesson:
                changes.append(
                    f"✏️ Замена\n<b>{day_name}, {week_day}</b>, пара {pair_num}\n"
                    f"Было: \n⏱️<code>{old_lesson['время'].replace('ауд.', ' | ауд.')}\n</code>📚{old_lesson['пара'].replace('ауд.', ' | ауд.')}\n"  # type:ignore
                    f"Стало: \n⏱️<code>{new_lesson['время']}\n</code>📚{new_lesson['пара'].replace('ауд.', ' | ауд.')}\n"  # type:ignore
                )
                changes.append("_________________________________\n")

    header = "🔔 Изменения в расписании:\n\n"
    return header + "\n".join(changes)


async def changes_monitoring(
    http_session: aiohttp.ClientSession, session_maker, bot: aiogram.Bot
) -> None:

    await asyncio.sleep(10)
    local_week = int(WeekState.week)

    while True:
        notify_users = NotifyUsers(bot)

        async with session_maker() as session:
            schedule_serv = ScheduleService(session)
            user_service = UserService(session)
            week: int = WeekState.week

            try:
                week: int = WeekState.week
                time_now = datetime.now(TZ_SAMARA)

                rows = await schedule_serv.get_groups_id(week)  # [(id1, id2, id3)]
                logger.debug(f"rows is... {rows}")

                if rows:
                    for row in rows[0]:  # row here is group id
                        new_schd = await HTTPScheduleParser.parse(http_session, row, local_week)
                        await date_setter(new_schd, False, time_now)
                        new_hash = schedule_hash(new_schd)

                        data = await schedule_serv.get_schedule_and_hash(
                            week, row
                        )  # [( [{}], 'str')]

                        old_schd = data[0][0]  # type:ignore
                        old_hash = data[0][1]  # type:ignore

                        if old_schd is None or old_hash is None:
                            logger.info(f"Schedule is None for  {row} at {week}... why?")
                            continue

                        if new_hash == old_hash:
                            update = {
                                "last_updated_formated": time_now.strftime("%d %B %H:%M"),
                                "last_updated": int(time_now.timestamp()),
                            }
                            await schedule_serv.update_schedule_in_monitoring(
                                local_week, row, update
                            )
                            continue

                        else:
                            logger.info(f"Schedule changed for {row}... starting alarm")
                            changes = await schedule_diff_seeker(old_schd, new_schd)
                            users = await user_service.get_all_users_in_group(row)

                            to_update = {
                                "schedule_json": new_schd,
                                "hash": new_hash,
                                "last_updated": int(time_now.timestamp()),
                                "last_updated_formated": time_now.strftime("%d %B %H:%M"),
                            }

                            await schedule_serv.update_schedule_in_monitoring(
                                local_week, row, to_update
                            )
                            logger.debug("Updated")
                            await notify_users.send(users, changes, bot)

                        await asyncio.sleep(10)

                if local_week == WeekState.week:
                    local_week += 1
                else:
                    local_week = WeekState.week

            except asyncio.CancelledError:
                raise

            except Exception as e:
                logger.warning(f"Problem with monitoring... {e}")
                await asyncio.sleep(60)  # 60

        await asyncio.sleep(1800)
