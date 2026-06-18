import re
from datetime import datetime, timedelta

import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from config import TZ_SAMARA, WeekState
from parse import HTTPScheduleParser

from .service_classes import GroupService, ScheduleService, UserService


# we use this to get normal keys from database. actually im not sure if we really need that, but legacy code didnt worked without it
# so let is just be
async def output_formatter(raw) -> list | dict | None:
    if isinstance(raw, list):
        for day in raw:
            old_lst = day["lessons"]
            day["lessons"] = {int(key): value for key, value in old_lst.items()}
        return raw

    if isinstance(raw, dict):
        old_lst = raw.get("lessons", {})
        raw["lessons"] = {int(key): value for key, value in old_lst.items() if str(key).isdigit()}
        return raw


# wee need to activate parse_mode='HTML' in message.answer
# I DONT UNDERTSTAND WHY WE USE CHECK TO IF LN < 2? SO I COMMENT It, MAybe one day well nedd thath
icons = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


async def message_maker(raw: list | dict) -> str:
    temp_msg = ""
    temp_msg = ""

    if isinstance(raw, dict):
        raw = [raw]
    if isinstance(raw[0], list):
        raw = raw[0]

    for day in raw:
        ln = len(day["lessons"])
        logger.info(f"day is {day}")

        if ln < 2 and day["lessons"].get(1, {}).get("пара", 0) != "Выходной":
            continue

        temp_msg += f"📅<b>{day['day_name']}</b>, "
        temp_msg += f"{day['week_day']}\n"

        for lesson in range(1, ln + 1):
            temp_msg += f"\n{icons[lesson - 1]}\u200b<b><code>{day['lessons'][lesson]['время']}</code></b>\n"
            ls_type = re.search(r"\((.*?)\)", day["lessons"][lesson]["пара"])
            emoji = "📚"

            if ls_type:
                ls_type_found = ls_type.group(1)
                match ls_type_found:
                    case "лекция":
                        emoji = "📚"
                    case "практика":
                        emoji = "✏️"
                    case "лаба":
                        emoji = "🔬"

            parts = day["lessons"][lesson]["пара"].split("ауд.")
            ln = len(parts)
            if ln < 2 and day["lessons"].get(1, {}).get("пара", 0) == "Выходной":
                parts.append("\tДиван")
            elif ln < 2:
                parts.append("\tне указана")

            temp_msg += f"{emoji}{parts[0].strip()}\n📍ауд.{parts[1]}\n"
        temp_msg += "\n"
        temp_msg += "_________________________________\n\n"

    return temp_msg


# today here is time_now. i made it argument because dont like fact that we use time three times
async def date_setter(no_date_schedule: list, is_next: bool, today) -> None:
    start_of_week = today - timedelta(days=today.weekday())
    if is_next:
        start_of_week += timedelta(days=7)
    i = 0

    for cell in no_date_schedule:
        day = start_of_week + timedelta(days=i)
        cell["week_day"] = day.strftime("%d %B")
        i = i + 1


async def schedule_week_service(
    message: Message, session: AsyncSession, http_session: aiohttp.ClientSession, is_next_week=False
) -> list | dict | None:
    try:
        from utils import schedule_hash

        user_service = UserService(session)

        group_id = await user_service.get_user_group(message.chat.id)
        logger.debug(f"Group id is {group_id}")
        if group_id is None:
            return None

        ScheduleServ = ScheduleService(session)
        week = WeekState.week
        time_now = datetime.now(TZ_SAMARA)

        if is_next_week == True:
            week += 1

        schd = await output_formatter(await ScheduleServ.get_schedule(week, group_id))

        if schd is None:
            logger.info(f"trying to parse with week {week} amd group {group_id}")
            schd = await HTTPScheduleParser.parse(http_session, group_id, week)
            logger.debug(f"schedule just after parse... {schd}")

            await date_setter(schd, is_next_week, time_now)
            time_now_seconds = int(time_now.timestamp())
            hash = schedule_hash(schd)
            to_insert = (
                group_id,
                week,
                schd,
                hash,
                time_now_seconds,
                time_now.strftime("%d %B %H:%M"),
            )  # type:ignore

            await ScheduleServ.insert_schedule(session, to_insert)
            logger.info(f"New schedule was added for {group_id} with {week} week")

        return schd
    except Exception as e:
        logger.exception("Problem with sending schedule service...", e)


days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


async def schedule_day_service(
    message: Message, session: AsyncSession, http_session: aiohttp.ClientSession, is_next_day=False
) -> list | None | str:
    try:
        logger.debug("Started the schedule service")
        time_now = datetime.now(TZ_SAMARA)

        if is_next_day:
            time_now += timedelta(days=1)

        if time_now.weekday() == 0 and is_next_day:
            schd = await schedule_week_service(message, session, http_session, True)
        else:
            schd = await schedule_week_service(message, session, http_session, False)

        if schd is None:
            return "Выходной"
        for day in schd:
            if days[time_now.weekday()] in day.values():
                if len(day.get("lessons", 0)) == 0:
                    day["lessons"] = {1: {"пара": "Выходной", "время": "Отсутствует"}}

                return [day]

    except Exception as e:
        logger.exception("Problem with sending schedule service...", e)
