import os
from dotenv import load_dotenv
from pathlib import Path

from loguru import logger
from enum import Enum

CURRENT_FILE_PATH = Path(__file__).resolve()
SRC_DIR = next(p for p in CURRENT_FILE_PATH.parents if p.name == 'src')
DOTENV_PATH = SRC_DIR /'.env'




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

    BOT_TOKEN=os.getenv('BOT_TOKEN')
    ALL_GROUPS_LINK=os.getenv("GET_GROUPS_LINK")
    SITE_LINK=os.getenv("SITE_LINK")


    DATABASE_URL = f"pstgresql+asyncpg://{USER}:{PASSWORD}@{HOST}/{DBNAME}"

except Exception as e:
    logger.error(f'Cant load .env data {e}', exc_info=True)
    raise RuntimeError
