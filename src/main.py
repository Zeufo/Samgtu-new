from os import setuid
from loguru import logger
import sys
from process import Process
from database import PostgresConnect
import asyncio




def setup_logger() -> None:
    logger.remove()

    logger.add(
        sys.stderr, 
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"  # В консоль пишем только INFO и выше
    )

    logger.add(
        'logs/bot.log',
        rotation='25mb',
        retention='10 days',
        compression='zip',)




async def main():
    setup_logger()
    pool  = PostgresConnect.get_pool()
    MainProcess = Process()
    await MainProcess.preparation(pool, True)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass

