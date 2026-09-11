import abc
import asyncio

import aiogram
from loguru import logger


class Notifier(abc.ABC):
    @abc.abstractmethod
    async def send(self, target_id: tuple[int], text: str, service) -> None:
        pass


class NotifyUsers(Notifier):
    def __init__(self, service: aiogram.Bot):
        self.service = service

    async def send(self, target_id: tuple[int], text: str, service: aiogram.Bot) -> None:
        logger.info(f"target id is... {target_id}")

        for user in target_id:
            try:
                await service.send_message(user, text, parse_mode="HTML")
                await asyncio.sleep(0.3)

            except Exception as e:
                logger.warning(f"problem found! {e}")
