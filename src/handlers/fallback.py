from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import GITHUB_LINK
from services import welcome

# /help and /github
router = Router(name=__name__)


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        """Неизвестная команда\n
/start начать
/commands посмотреть список команд
"""
    )
