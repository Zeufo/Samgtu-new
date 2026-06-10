from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
import asyncio

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types

from services import welcome



router = Router(name=__name__)

@router.message(CommandStart())
@router.message(Command('начать', 'изменитьмоюгруппу', ignore_case=True))
@router.message(F.text.replace(' ', '').upper().in_({'СТАРТ', 'НАЧАТЬ', 'ИЗМЕНИТЬМОЮГРУППУ'}))
async def say_hello(message: Message, state: FSMContext) -> None:
    await welcome(message, state)
    #await state.set_state(RegistartionUser.faculty_name)

