import abc
import time
import typing

import aiohttp
from loguru import logger

from config import ALL_GROUPS_LINK, SCHD_LINK, SITE_LINK
from parse.datacleaner import clean_schedule, faculties_formatter, parse_groups_formatter


class Parser(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    async def parse(*args, **kwargs) -> typing.Any:
        pass


@typing.final
class HTTPFacultyParser(Parser):
    @staticmethod
    async def parse(session) -> list:
        while True:
            try:
                async with session.get(SITE_LINK) as response:
                    raw = await response.text()

                    return faculties_formatter(raw)

            except Exception as e:
                logger.exception(f"Unexpected error in parsing faculties...", e)
                time.sleep(1)


@typing.final
class HTTPGroupParser(Parser):
    @staticmethod
    async def parse(session: aiohttp.ClientSession, faculties_id: list) -> list:
        collect_groups = await parse_groups_formatter()

        for faculty in faculties_id:
            logger.info(f"parsing for {faculty} ")
            for course in range(1, 7):
                try:
                    formated_link = ALL_GROUPS_LINK.format(course=f"{course}", faculty=f"{faculty}")

                    logger.debug(f"link is  {formated_link} ")

                    async with session.get(formated_link) as response:
                        data = await response.json(content_type=None)
                        await collect_groups(data, course, faculty)

                    time.sleep(0.2)

                except Exception as e:
                    logger.exception(f"Unexpected error in parsing faculties... Trying another", e)
                    continue

        total = await collect_groups([], 0, 0, True)
        del collect_groups

        return total  # type: ignore
        # IT cant be None because we call the func above. so no matter what we always have [] even if there were zero groups


@typing.final
class HTTPScheduleParser(Parser):
    @staticmethod
    async def parse(session: aiohttp.ClientSession, grp_id: int | str, weeknum: int) -> list:
        try:
            if isinstance(grp_id, str):
                grp_id = int(grp_id)

            formated_link = SCHD_LINK.format(groupid=grp_id, weeknumber=weeknum)
            logger.debug(f"formated link is  {formated_link}")

            timeout = aiohttp.ClientTimeout(total=10)

            async with session.get(formated_link, timeout=timeout) as response:
                raw: list
                raw = await clean_schedule(response)
                return raw

        except Exception as e:
            logger.error("Cant parse the schedule...", e)
            raise RuntimeError
