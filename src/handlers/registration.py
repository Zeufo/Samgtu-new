from aiogram import Router
from aiogram.filters import KICKED, MEMBER, ChatMemberUpdatedFilter, Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatMemberUpdated, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from services.registration_service import (
    RegistartionUser,
    delete_user_cause_block,
    get_user_faculty_service,
    get_user_group_service,
    write_user_service,
)

router = Router(name=__name__)


@router.message(RegistartionUser.waiting_for_faculty)
async def get_user_faculty(message: Message, state: FSMContext) -> None:
    await get_user_faculty_service(message, state)


@router.message(RegistartionUser.waiting_for_group)
async def get_user_group(message: Message, state: FSMContext) -> None:
    await get_user_group_service(message, state)


@router.message(RegistartionUser.write_in_base)
async def write_user(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await write_user_service(message, state, session)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated):
    user_id = int(event.from_user.id)
    await delete_user_cause_block(user_id)
    logger.debug(f"user {user_id} was deleted")
