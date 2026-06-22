import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from loguru import logger

CURRENT_FILE_PATH = Path(__file__).resolve()
SRC_DIR = next(p for p in CURRENT_FILE_PATH.parents if p.name == "src")
DOTENV_PATH = SRC_DIR.parent / ".env"


@dataclass
class WeekState:
    week: int = 0


TZ_SAMARA = ZoneInfo("Europe/Samara")


try:
    load_dotenv(dotenv_path=DOTENV_PATH)

    DBNAME = os.getenv("DB_NAME")
    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASSWORD")
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")

    BOT_TOKEN = os.environ["TEST_BOT_TOKEN"]
    PROXY_LINK = os.environ["PROXY_LINK"]

    ALL_GROUPS_LINK = "https://samgtu.ru/students/getgrouplist?Course={course}&Faculty={faculty}"
    SITE_LINK = "https://samgtu.ru/students/schedule"
    SCHD_LINK = "https://samgtu.ru/students/getschedule?GroupID={groupid}&WeekNumber={weeknumber}"
    GITHUB_LINK = os.getenv("GITHUB_LINK", "неуказано")

    DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}/{DBNAME}"

except Exception as e:
    logger.error(f"Cant load .env data {e}", exc_info=True)
    raise RuntimeError
