from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from config import GITHUB_LINK
from services import (
    NotifyUsers,
    ScheduleService,
    UserService,
    count_active_users,
    date_setter,
    welcome,
)


async def count_active_users() -> int:
    users = await UserService.get_all_users()
    return users
