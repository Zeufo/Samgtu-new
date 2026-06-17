import abc
import aiogram
from loguru import logger
import asyncio

class Notifier(abc.ABC):
    @abc.abstractmethod
    async def send(self, target_id: tuple[int], text: str, service) -> None:
        pass



class NotifyUsers(Notifier):
    def __init__(self, service: aiogram.Bot):
        self.service = service

    async def send(self, target_id: tuple[int], text: str, service: aiogram.Bot) -> None:
        for user in target_id:
            try:
                await service.send_message(user, text)
                await asyncio.sleep(0.2)

            except Exception as e:
                logger.info(f'user {user} has blocked the bot, cant inform...')
                
