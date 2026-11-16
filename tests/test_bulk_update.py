import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import Schedule
from services import ScheduleService


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Schedule.__table__.create)

    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_bulk_update_full_schedule_and_time(session):
    """Bulk-update не должен падать на synchronize_session и должен обновлять строку."""
    session.add(
        Schedule(
            group_id=101,
            week_num=1,
            schedule_json=[{"day_name": "Понедельник", "lessons": {}}],
            hash="old",
            last_updated=1,
            last_updated_formated="old",
        )
    )
    await session.commit()

    schedule_service = ScheduleService(session)

    full_updates = [
        {
            "group_id": 101,
            "week_num": 1,
            "schedule_json": [{"day_name": "Вторник", "lessons": {}}],
            "hash": "new",
            "old_hash": "old",
            "last_updated": 2,
            "last_updated_formated": "new",
        }
    ]
    time_updates = [
        {
            "group_id": 101,
            "week_num": 1,
            "last_updated": 3,
            "last_updated_formated": "newer",
        }
    ]

    async with session.begin():
        await schedule_service.bulk_update_full_schedule(full_updates, commit=False)
        await schedule_service.bulk_update_only_time(time_updates, commit=False)

    session.expire_all()
    row = await session.get(Schedule, 1)

    assert row is not None
    assert row.hash == "new"
    assert row.schedule_json == [{"day_name": "Вторник", "lessons": {}}]
    assert row.last_updated == 3
    assert row.last_updated_formated == "newer"


@pytest.mark.asyncio
async def test_bulk_update_full_schedule_respects_old_hash(session):
    """Оптимистичная блокировка не даёт перезаписать строку с другим хешем."""
    session.add(
        Schedule(
            group_id=101,
            week_num=1,
            schedule_json=[{"day_name": "Понедельник", "lessons": {}}],
            hash="actual",
            last_updated=1,
            last_updated_formated="old",
        )
    )
    await session.commit()

    schedule_service = ScheduleService(session)
    updates = [
        {
            "group_id": 101,
            "week_num": 1,
            "schedule_json": [{"day_name": "Вторник", "lessons": {}}],
            "hash": "new",
            "old_hash": "stale",
            "last_updated": 2,
            "last_updated_formated": "new",
        }
    ]

    async with session.begin():
        await schedule_service.bulk_update_full_schedule(updates, commit=False)

    session.expire_all()
    row = await session.get(Schedule, 1)

    assert row is not None
    assert row.hash == "actual"
    assert row.schedule_json == [{"day_name": "Понедельник", "lessons": {}}]
