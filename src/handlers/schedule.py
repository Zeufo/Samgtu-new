import asyncio
from aiogram import Router, types
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import F

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types

from database.models import AsyncSessionLocal
from services  import schedule_this_week_service

router = Router(name=__name__)


@router.message(F.text.upper().replace(' ', '') == "НАНЕДЕЛЮ")
async def schedule_this_week(message: Message, session: AsyncSession) -> None:
    await schedule_this_week_service(message, session) 

@router.message(F.text.upper().replace(' ', '') == "НАСЛЕД.НЕДЕЛЮ")
async def schedule_next_week(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pass

@router.message(F.text.upper().replace(' ', '') == "НАСЕГОДНЯ")
async def schedule_this_day(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pass

@router.message(F.text.upper().replace(' ', '') == "НАЗАВТРА")
async def schedule_next_day(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pass

