from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import GITHUB_LINK
from services import welcome

# /help and /github
router = Router(name=__name__)


@router.message(Command("help", ignore_case=True))
@router.message(CommandStart())
@router.message(Command("начать", "изменитьмоюгруппу", ignore_case=True))
@router.message(F.text.replace(" ", "").upper().in_({"СТАРТ", "НАЧАТЬ", "ИЗМЕНИТЬМОЮГРУППУ"}))
async def say_hello(message: Message, state: FSMContext) -> None:
    await welcome(message, state)


@router.message(Command("info", ignore_case=True))
@router.message(Command("about", ignore_case=True))
async def info(message: Message) -> None:
    await message.answer(
        f"""Некоммерческий Open Source проект, созданный силами студентов для улучшения качества образовательной среды.
\nИсходный код и документация доступны на GitHub:\n{GITHUB_LINK}

Проект улучшается по мере увеличения наших сил и возможностей
        """
    )


@router.message(Command("commands", ignore_case=True))
async def commands(message: Message) -> None:
    await message.answer(
        f"""/start начать
/commands список команд
/info и /about информация о проекте

/settings настройки (не реализовано)

/week расписание на неделю
/today расписание на день
/tomorrow расписание на завтра
/nextweek
        """
    )
