import asyncio
from aiogram import Router, types
from aiogram.types import Message

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types

from handlers.service import RegistartionUser
from handlers.service import get_user_faculty_service, get_user_group_service, write_user_service


router = Router(name=__name__)


@router.message(RegistartionUser.waiting_for_faculty)
async def get_user_faculty(message: Message, state: FSMContext) -> None:
    await get_user_faculty_service(message, state)


@router.message(RegistartionUser.waiting_for_group)
async def get_user_group(message: Message, state: FSMContext) -> None:
    await get_user_group_service(message, state)

@router.message(RegistartionUser.write_in_base)
async def write_user(message: Message, state: FSMContext) -> None:
    await write_user_service(message, state)

