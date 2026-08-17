from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from config import GITHUB_LINK
from services import NotifyUsers, ScheduleService, UserService, date_setter, welcome

# /help and /github
router = Router(name=__name__)


class AdminCommands(StatesGroup):
    waiting_for_command = State()


@router.message(Command("admin_count", ignore_case=True))
async def count_users(message: Message) -> None:
    users = await count_users()
    return users


@router.message(Command("admin_send_everyone", ignore_case=True))
async def info(message: Message) -> None:
    pass


@router.message(Command("admin_send_specific", ignore_case=True))
async def info(message: Message) -> None:
    pass
