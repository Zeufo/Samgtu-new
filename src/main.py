from loguru import logger
import sys
from process import Process
from database import PostgresConnect
import asyncio




def setup_logger() -> None:
    logger.remove()

    logger.add(
        sys.stderr, 
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <6}</level> | {message}",
        level="INFO",  # В консоль пишем только INFO и выше
        backtrace=False,
        diagnose=False
    )

    logger.add(
        'logs/bot.log',
        rotation='25mb',
        retention='10 days',
        compression='zip',)



async def main():

    print("Main started!")

    setup_logger()
    pool = await PostgresConnect.get_async_pool()
    MainProcess = Process()
    await MainProcess.preparation(pool, True)


if __name__ == "__main__":
    try:
        pass
        asyncio.run(main())

    except KeyboardInterrupt:
        pass

