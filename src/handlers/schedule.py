import asyncio

import aiohttp
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AsyncSessionLocal
from keyboards import admit_decline_kb, schedule_kb
from services import message_maker, schedule_day_service, schedule_week_service

router = Router(name=__name__)


async def make_and_send(message: Message, to_transform):
    logger.debug("Now in make and send")

    if to_transform is None:
        await message.answer("Пожалуйста, пройдите регистрацию\n/start")
        return

    logger.debug(f"Now in make and send check passed with to_transform {to_transform}")
    to_send = await message_maker(to_transform)  # type:ignore

    if len(to_send) == 0:
        await message.answer("Похоже, что пары на указанной неделе отсутствуют")  # type:ignore
        return

    await message.answer(to_send, parse_mode="HTML")  # type:ignore


@router.message(Command("week", ignore_case=True))
@router.message(F.text.upper().replace(" ", "") == "НАНЕДЕЛЮ")
async def schedule_this_week(
    message: Message, session: AsyncSession, http_session: aiohttp.ClientSession
) -> None:
    raw_msg = await schedule_week_service(message, session, http_session, False)
    await make_and_send(message, raw_msg)
    logger.debug("На след. неделю сработало")


@router.message(F.text.upper().replace(" ", "") == "НАСЛЕД.НЕДЕЛЮ")
async def schedule_next_week(
    message: Message, session: AsyncSession, http_session: aiohttp.ClientSession
) -> None:
    raw_msg = await schedule_week_service(message, session, http_session, True)
    await make_and_send(message, raw_msg)
    logger.debug("На след. неделю сработало")


@router.message(Command("today", ignore_case=True))
@router.message(F.text.upper().replace(" ", "") == "НАСЕГОДНЯ")
async def schedule_this_day(
    message: Message, session: AsyncSession, http_session: aiohttp.ClientSession
) -> None:
    raw_msg = await schedule_day_service(message, session, http_session, False)
    await make_and_send(message, raw_msg)
    logger.debug("На сегодня")


@router.message(Command("tomorrow", ignore_case=True))
@router.message(F.text.upper().replace(" ", "") == "НАЗАВТРА")
async def schedule_next_day(
    message: Message, session: AsyncSession, http_session: aiohttp.ClientSession
) -> None:
    raw_msg = await schedule_day_service(message, session, http_session, True)
    await make_and_send(message, raw_msg)
    logger.debug("На завтра")
