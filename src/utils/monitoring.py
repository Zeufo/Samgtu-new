import asyncio
import hashlib
import json
import typing
from datetime import datetime

import aiogram
import aiohttp
import bs4
from loguru import logger
from sqlalchemy.sql.functions import grouping_sets

from config import PROXY_LINK, SITE_LINK, TZ_SAMARA, WeekState
from parse import HTTPScheduleParser
from services import NotifyUsers, ScheduleService, UserService, date_setter


async def week_changes_monitoring(http_session: aiohttp.ClientSession) -> None:
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

    except Exception as e:
        logger.warning("Problem with week monitoring...", e)


def schedule_hash(schedule: list) -> str:
    raw = json.dumps(schedule, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


async def schedule_diff_seeker(old: list, new: list) -> str:
    # logger.debug(f"old is {old}")
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


@typing.final
class ChangesProccess:
    def __init__(
        self,
        http_session: aiohttp.ClientSession,
        session_maker,
        bot: aiogram.Bot,
        NOTIFICATIONS_ENABLED: bool = False,
    ) -> None:

        self.http_session = http_session
        self.session_maker = session_maker
        self.bot = bot
        self.notification_status = NOTIFICATIONS_ENABLED
        self.time_now = datetime.now(TZ_SAMARA)

    async def start_checking(self) -> None:
        while True:
            await week_changes_monitoring(self.http_session)
            week: int = WeekState.week
            self.time_now = datetime.now(TZ_SAMARA)

            await self._schedule_changes_monitoring_cycle(week)
            await self._schedule_changes_monitoring_cycle(week + 1, True)

            await asyncio.sleep(1200)

    async def _find_groups_with_changes_and_process(
        self,
        groups_and_hashes: dict,
        to_update_full: list,
        to_update_time: list,
        week: int,
        is_next: bool,
    ) -> None:

        for group in groups_and_hashes.keys():
            try:
                await asyncio.sleep(0.3)  # antiflood
                new_schd = await HTTPScheduleParser.parse(self.http_session, group, week)
                await date_setter(new_schd, is_next, self.time_now)
                new_hash = schedule_hash(new_schd)

                if new_hash != groups_and_hashes.get(group):
                    to_update_full.append(
                        {
                            "group_id": group,
                            "week_num": week,
                            "schedule_json": new_schd,
                            "hash": new_hash,
                            "last_updated": int(self.time_now.timestamp()),
                            "last_updated_formated": self.time_now.strftime("%d %B %H:%M"),
                        }
                    )
                else:
                    to_update_time.append(
                        {
                            "group_id": group,
                            "week_num": week,
                            "last_updated": int(self.time_now.timestamp()),
                            "last_updated_formated": self.time_now.strftime("%d %B %H:%M"),
                        }
                    )

            except Exception as e:
                logger.warning(f"Problem with parsing {group} at {week}... {e}")

    async def _schedule_changes_monitoring_cycle(
        self,
        week: int,
        is_next: bool = False,
    ) -> None:
        async with self.session_maker() as session:
            schedule_service = ScheduleService(session)
            groups_and_hashes = (
                await schedule_service.get_every_groups_id_with_hashes_in_one_dict_for_week(week)
            )

        to_update_full = []
        to_update_time = []

        await self._find_groups_with_changes_and_process(
            groups_and_hashes, to_update_full, to_update_time, week, is_next
        )

        async with self.session_maker() as session:
            schedule_service = ScheduleService(session)
            await schedule_service.bulk_update_full_schedule(to_update_full)
            await schedule_service.bulk_update_only_time(to_update_time)

        diff = await schedule_diff_seeker()

    async def _notify(): ...


async def find_groups_with_changes_and_not(
    http_session: aiohttp.ClientSession,
    groups_and_hashes: dict,
    no_changes: list,
    with_changes: list,
    time_now: datetime,
    week: int,
    is_next: bool,
) -> None:

    for group in groups_and_hashes.keys():
        try:
            await asyncio.sleep(0.1)  # because im not sure where is flood limit
            new_schd = await HTTPScheduleParser.parse(http_session, group, week)
            await date_setter(new_schd, is_next, time_now)
            new_hash = schedule_hash(new_schd)

            if new_hash != groups_and_hashes.get(group):
                with_changes.append(group)
            else:
                no_changes.append(group)

        except Exception as e:
            logger.warning(f"Problem with parsing {group} at {week}... {e}")


async def schedule_changes_pipeline(
    http_session: aiohttp.ClientSession,
    session_maker,
    bot: aiogram.Bot,
    NOTIFICATIONS_ENABLED: bool = False,
) -> None:
    while True:
        await week_changes_monitoring(http_session)
        week: int = WeekState.week
        time_now = datetime.now(TZ_SAMARA)

        await schedule_changes_monitoring_cycle(
            http_session, session_maker, bot, week, False, time_now, NOTIFICATIONS_ENABLED
        )

        await schedule_changes_monitoring_cycle(
            http_session, session_maker, bot, week + 1, True, time_now, NOTIFICATIONS_ENABLED
        )
        await asyncio.sleep(3600)


async def schedule_changes_monitoring_cycle(
    http_session: aiohttp.ClientSession,
    session_maker,
    bot: aiogram.Bot,
    week: int,
    is_next: bool,
    time_now: datetime,
    NOTIFICATIONS_ENABLED: bool = False,
) -> None:
    async with session_maker() as session:
        schedule_service = ScheduleService(session)
        groups_and_hashes = (
            await schedule_service.get_every_groups_id_with_hashes_in_one_dict_for_week(week)
        )

    groups_no_changes = []
    groups_with_changes = []

    await find_groups_with_changes_and_not(
        http_session,
        groups_and_hashes,
        groups_no_changes,
        groups_with_changes,
        time_now,
        week,
        is_next,
    )


async def changes_monitoring(
    http_session: aiohttp.ClientSession,
    session_maker,
    bot: aiogram.Bot,
    NOTIFICATIONS_ENABLED: bool = False,
) -> None:
    await asyncio.sleep(10)
    local_week = int(WeekState.week)
    is_next = False
    while True:
        notify_users = NotifyUsers(bot)

        async with session_maker() as session:
            schedule_serv = ScheduleService(session)
            user_service = UserService(session)
            week: int = WeekState.week

            try:
                week: int = WeekState.week
                time_now = datetime.now(TZ_SAMARA)

                rows = await schedule_serv.get_groups_id(local_week)  # [(id1, id2, id3)]
                logger.debug(f"rows is... {rows}")

                if rows:
                    for group in rows:  # row here is group id
                        await asyncio.sleep(1)

                        row = group[0]
                        logger.debug(f"checking for {row}")

                        try:
                            new_schd = await HTTPScheduleParser.parse(http_session, row, local_week)
                        except Exception as e:
                            logger.warning(f"Problem with parsing {row} at {local_week}... {e}")
                            continue

                        await date_setter(new_schd, is_next, time_now)
                        new_hash = schedule_hash(new_schd)

                        data = await schedule_serv.get_schedule_and_hash(
                            local_week, row
                        )  # [( [{}], 'str')]

                        old_schd = data[0][0]  # type:ignore
                        old_hash = data[0][1]  # type:ignore

                        if (
                            old_schd is None or old_hash is None
                        ):  # Эт кстати очень плохо. в начале года руинит если расписания нет
                            logger.info(f"Schedule is None for  {row} at {week}... why?")
                            if new_schd:
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

                                if NOTIFICATIONS_ENABLED:
                                    logger.info(f"NOTIFY {row} group")
                                    changes = "Обнаружено изменение в расписании!\nПохоже поставили пары.\nРазраб криворукий, поэтому, пожалуйста, проверьте сами.\n /week\n/nextweek"
                                    users = await user_service.get_all_users_in_group(row)
                                    if users and NOTIFICATIONS_ENABLED:
                                        await notify_users.send(users, changes, bot)

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
                            logger.warning(f"Schedule changed for {row}... starting alarm")

                            changes = await schedule_diff_seeker(old_schd, new_schd)

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

                            if NOTIFICATIONS_ENABLED:
                                users = await user_service.get_all_users_in_group(row)
                                logger.info(f"users for notify is {users}")
                                if users and NOTIFICATIONS_ENABLED:
                                    await notify_users.send(users, changes, bot)

                        await asyncio.sleep(2)

                if local_week == WeekState.week:
                    local_week += 1
                    is_next = True
                else:
                    local_week = WeekState.week
                    is_next = False
            except asyncio.CancelledError:
                raise

            except Exception as e:
                logger.warning(f"Problem with monitoring... {e}")
                await asyncio.sleep(60)  # 60

        await asyncio.sleep(1800)
