from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_ID, GITHUB_LINK
from services import (
    NotifyUsers,
    ScheduleService,
    UserService,
    count_active_users,
    date_setter,
    welcome,
)

# /help and /github
router = Router(name=__name__)


class AdminCommands(StatesGroup):
    waiting_for_command = State()


async def is_user_admin(message: Message) -> bool:
    if message.chat.id == ADMIN_ID:
        return True
    else:
        await message.answer("Только для администратора.")
        return False


@router.message(Command("admin_count", ignore_case=True))
async def count_users(message: Message) -> None:
    if not is_user_admin(message):
        return
    users = await count_active_users()
    await message.answer(str(users))


admin_commands = """
1./admin_commands
2./admin_send_everyone
3./admin_count
"""


@router.message(Command("admin_commands", ignore_case=True))
async def admin_commands_list(message: Message) -> None:
    if not is_user_admin(message):
        return
    await message.answer(admin_commands)


@router.message(Command("admin_send_everyone", ignore_case=True))
async def send_everyone(message: Message, state: FSMContext) -> None:
    if not is_user_admin(message):
        return

    await message.answer("Введите сообщение (exit для отмены)")
    await state.set_state(AdminCommands.waiting_for_command)


@router.message(AdminCommands.waiting_for_command)
async def send_message(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text == "exit":
        await message.answer("Отменено.")
        await state.clear()
        return

    users = await UserService.get_all_users()
    notify = NotifyUsers(bot)
    await notify.send(users, message.text, bot)  # type:ignore
    await message.answer("Отправлено")
    await state.clear()


@router.message(Command("admin_send_specific", ignore_case=True))
async def info(message: Message) -> None:
    pass
