import asyncio
import typing

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from loguru import logger
from sqlalchemy import and_, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from database import Group, Schedule, User
from database.models import AsyncSessionLocal
from keyboards import admit_decline_kb, schedule_kb


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_user(
        self,
        user_id: int,
        course: int,
        faculty: str,
        group_id: int,
        last_time_active: str,
    ) -> User:

        new_user = User(
            user_id=user_id,
            course=course,
            faculty=faculty,
            group_id=group_id,
            last_time_active=last_time_active,
        )

        stmt = insert(User).values(
            user_id=user_id,
            course=course,
            faculty=faculty,
            group_id=group_id,
            last_time_active=last_time_active,
        )

        # if user exists set this values at...
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"],
            set_={
                "course": stmt.excluded.course,
                "faculty": stmt.excluded.faculty,
                "group_id": stmt.excluded.group_id,
                "last_time_active": stmt.excluded.last_time_active,
            },
        )

        await self.session.execute(stmt)
        await self.session.commit()
        return new_user

    async def get_user_group(self, user_id: int) -> int | None:
        query = select(User.group_id).where(User.user_id == user_id)
        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def get_all_users_in_group(self, group_id: int):

        query = select(User.user_id).where(User.group_id == group_id)
        result = await self.session.execute(query)

        result = (result.tuples().all())[0]
        logger.debug(f"result is {result}")
        return result


class GroupService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_id(self, group_name: str, course: int) -> int | None:  # for registration
        query = select(Group.group_id).where(
            and_(Group.group_name == group_name, Group.course == course)
        )
        result = await self.session.execute(query)

        return result.scalar_one_or_none()


class ScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_schedule(self, week: int, group: int) -> list[typing.Any] | None:
        query = select(Schedule.schedule_json).where(
            and_(Schedule.group_id == group, Schedule.week_num == week)
        )
        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def get_schedule_and_hash(
        self, week: int, group: int
    ) -> list[typing.Any] | None | typing.Any:
        query = select(Schedule.schedule_json, Schedule.hash).where(
            and_(Schedule.group_id == group, Schedule.week_num == week)
        )
        result = await self.session.execute(query)
        return result.all()

    # to_insert = (group_id, WeekState.week, schd, "Not now", time_now_seconds, time_now.strftime('%d %B %H:%M'))#type:ignore
    async def insert_schedule(self, session: AsyncSession, to_insert: tuple) -> None:
        stmt = insert(Schedule).values(
            group_id=to_insert[0],
            week_num=to_insert[1],
            schedule_json=to_insert[2],
            hash=to_insert[3],
            last_updated=to_insert[4],
            last_updated_formated=to_insert[5],
        )
        await session.execute(stmt)
        await session.commit()

    async def update_schedule_in_monitoring(
        self, week: int, group_id: int, to_update: dict
    ) -> None:

        stmt = (
            update(Schedule)
            .where(and_(Schedule.group_id == group_id, Schedule.week_num == week))
            .values(**to_update)
            .execution_options(synchronize_session="fetch")
        )

        await self.session.execute(stmt)
        await self.session.commit()

    # this operation will be use in monitoring service so we take session from init
    async def get_groups_id(self, week: int):  # -> list |Result i guess
        query = select(Schedule.group_id).where(Schedule.week_num == week)
        result = await self.session.execute(query)

        return result.all()
