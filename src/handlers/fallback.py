from aiogram import Router
from aiogram.types import Message

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
