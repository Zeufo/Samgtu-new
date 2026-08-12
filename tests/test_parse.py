import aiohttp
import pytest
from aioresponses import aioresponses

from config import ALL_GROUPS_LINK, SCHD_LINK, SITE_LINK
from src.parse import HTTPGroupParser


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


async def test_parse_groups(session):
    fake_url = ALL_GROUPS_LINK
    fake_html = "<html><body><h1>Расписание</h1></body></html>"

    with aioresponses() as m:
        m.get(fake_url, status=200, body=fake_html)  # interceptor
        with pytest.raises(Exception):
            await HTTPGroupParser.parse(session, [])
