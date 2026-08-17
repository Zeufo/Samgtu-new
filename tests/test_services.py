import asyncio

import aiohttp
import pytest
from aioresponses import aioresponses

from src.services import ScheduleService


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session
