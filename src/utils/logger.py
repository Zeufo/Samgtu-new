from loguru import logger
import sys



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


setup_logger()
