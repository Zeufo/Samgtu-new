import os
from dotenv import load_dotenv
from pathlib import Path

from loguru import logger
from enum import Enum
from dataclasses import dataclass
from zoneinfo import ZoneInfo


CURRENT_FILE_PATH = Path(__file__).resolve()
SRC_DIR = next(p for p in CURRENT_FILE_PATH.parents if p.name == 'src')
DOTENV_PATH = SRC_DIR.parent /'.env'


@dataclass
class WeekState():
    week: int = 0



TZ_SAMARA = ZoneInfo('Europe/Samara')



#SHOULD DELETE THIS IF NO USE
class GroupsDictValues(Enum):
    ID = 0
    NAME = 1
    FACULTY = 3
    COURSE = 4



try:    
    load_dotenv(dotenv_path=DOTENV_PATH)
    
    DBNAME=os.getenv('DB_NAME')
    USER=os.getenv('DB_USER')
    PASSWORD=os.getenv('DB_PASSWORD')
    HOST=os.getenv('DB_HOST')
    PORT=os.getenv('DB_PORT')

    PROXY_LINK =os.environ["PROXY_LINK"]
    BOT_TOKEN=os.environ['TEST_BOT_TOKEN']
    ALL_GROUPS_LINK=os.environ["GET_GROUPS_LINK"]
    SITE_LINK=os.environ["SITE_LINK"]
    SCHD_LINK =os.environ['SCHD_LINK']

    DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}/{DBNAME}"

except Exception as e:
    logger.error(f'Cant load .env data {e}', exc_info=True)
    raise RuntimeError
