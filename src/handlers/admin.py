from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import ADMIN_ID
from services import (
    NotifyUsers,
    UserService,
    count_active_users,
)

# /help and /github
router = Router(name=__name__)


class AdminCommands(StatesGroup):
    waiting_for_command = State()
    waiting_for_id = State()


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
4./admin_send_one
"""


@router.message(Command("admin_commands", ignore_case=True))
async def admin_commands_list(message: Message) -> None:
    if not await is_user_admin(message):
        return
    await message.answer(admin_commands)


@router.message(Command("admin_send_everyone", ignore_case=True))
async def send_everyone(message: Message, state: FSMContext) -> None:
    if not await is_user_admin(message):
        return

    await message.answer("Введите сообщение (exit для отмены)")
    await state.set_state(AdminCommands.waiting_for_command)


@router.message(Command("admin_send_one", ignore_case=True))
async def send_one(message: Message, state: FSMContext) -> None:
    if not await is_user_admin(message):
        return

    await message.answer("Введите айди (exit для отмены)")
    await state.set_state(AdminCommands.waiting_for_id)


@router.message(AdminCommands.waiting_for_id)
async def get_target_id(message: Message, state: FSMContext) -> None:
    if message.text == "exit":
        await message.answer("Отменено")
        await state.clear()
        return

    if message.text:
        target_id = [int(message.text)]
        await state.update_data(target_id=target_id)
        await state.set_state(AdminCommands.waiting_for_command)


@router.message(AdminCommands.waiting_for_command)
async def send_message(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text == "exit":
        await message.answer("Отменено.")
        await state.clear()
        return

    data = await state.get_data()
    notify = NotifyUsers(bot)
    users = data.get("target_id", None)

    if not users:
        users = await UserService.get_all_users()

    await notify.send(users, message.text, bot)  # type:ignore
    await message.answer("Отправлено")
    await state.clear()


@router.message(Command("admin_send_specific", ignore_case=True))
async def info(message: Message) -> None:
    pass
