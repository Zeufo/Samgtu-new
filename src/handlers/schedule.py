import asyncio
from aiogram import Router, types
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import F

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types

from database.models import AsyncSessionLocal
from services import schedule_week_service, schedule_day_service, message_maker
from loguru import logger
import aiohttp

router = Router(name=__name__)


async def make_and_send(message: Message, to_transform):
    logger.info("Now in make and send")#---------------------------------------------------------------------------

    if to_transform is None:
        await message.answer("Пожалуйста, пройдите регистрацию")
        await message.answer("/start")
        return 

    logger.info("Now in make and send check passed")#---------------------------------------------------------------------------
    to_send = await message_maker(to_transform)#type:ignore
    await message.answer(to_send, parse_mode='HTML')#type:ignore




@router.message(F.text.upper().replace(' ', '') == "НАНЕДЕЛЮ")
async def schedule_this_week(message: Message, session: AsyncSession, http_session: aiohttp.ClientSession) -> None:
    raw_msg = await schedule_week_service(message, session, http_session, True) 
    await make_and_send(message, raw_msg)
    logger.info("На след. неделю сработало")




@router.message(F.text.upper().replace(' ', '') == "НАСЛЕД.НЕДЕЛЮ")
async def schedule_next_week(message: Message, session: AsyncSession, http_session: aiohttp.ClientSession) -> None:
    raw_msg = await schedule_week_service(message, session, http_session, True) 
    await make_and_send(message, raw_msg)
    logger.info("На след. неделю сработало")


@router.message(F.text.upper().replace(' ', '') == "НАСЕГОДНЯ")
async def schedule_this_day(message: Message, session: AsyncSession, http_session: aiohttp.ClientSession) -> None:
    raw_msg = await schedule_day_service(message, session, http_session)
    await make_and_send(message, raw_msg)
    logger.info("На сегодня")

@router.message(F.text.upper().replace(' ', '') == "НАЗАВТРА")
async def schedule_next_day(message: Message, session: AsyncSession, http_session: aiohttp.ClientSession) -> None:
    raw_msg = await schedule_day_service(message, session, http_session, True)
    logger.info(f'raw message for tommorow is {raw_msg}')#-----------------------------------------------------------------------
    await make_and_send(message, raw_msg)
    logger.info("На сегодня")
