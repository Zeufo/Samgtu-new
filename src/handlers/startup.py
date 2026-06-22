import aiohttp
import bs4
from aiogram import Router
from loguru import logger

from config import SITE_LINK, WeekState
from database import close_db

router = Router(name=__name__)


async def get_current_week_int(session: aiohttp.ClientSession) -> None:
    try:
        async with session.get(SITE_LINK) as response:
            data = await response.text()
            soup = bs4.BeautifulSoup(data, "html.parser")
            obj = soup.find("select", id="schedule_weektype_select")
            obj1 = obj.find("option", selected=True)  # type:ignore
            new_week = obj1["value"]  # type:ignore
            new_week: int
            WeekState.week = int(new_week)

    except Exception as e:
        logger.warning("Cant reach the number of week at first start")
        raise RuntimeError


@router.startup()
async def turn_on(http_session: aiohttp.ClientSession) -> None:
    logger.info("trying to get what week now...")
    await get_current_week_int(http_session)
    logger.info(f"week now... {WeekState.week}")


@router.shutdown()
async def turn_off() -> None:
    await close_db()
    logger.info("Database now closed")
