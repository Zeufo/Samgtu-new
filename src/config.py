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


USEFUL_LINKS: dict[str, str] = {
    # 📚 Учёба и официальные сервисы
    "https://lk.samgtu.ru": (
        "Личный кабинет студента — баллы, зачётки, долги и накопительная система."
    ),
    "https://samgtu.ru": ("Официальный сайт СамГТУ — приказы на стипендии, деканаты и документы."),
    "https://elib.samgtu.ru": (
        "Электронная библиотека (ЭБС) — методички к лабам, учебники и ГОСТы."
    ),
    # 🏛 Студенческая жизнь и помощь
    "https://samgtu.ru/social/social-politics-profkom": (
        "Профком студентов СамГТУ — матпомощь, путевки в лагеря, льготы и защита прав."
    ),
    "https://samgtu.ru/contacts": (
        "Контакты, карта и  адреса корпусов — чтобы не перепутать"
        "Здесь же реквизиты для оплаты обучения."
    ),
    # ⚙️ Проект
    "https://t.me/Zeufo": (
        "Обратная связь — сообщить об ошибке в расписании или предложить фичу.\nМожно анонимно через /feedback"
    ),
    "https://t.me/pod_samgtu"  : ("Паблик ТГ с чатами факультетов. Вопросы об обучение и прочие"),
    
}


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
    ADMIN_ID = int(os.getenv("ADMIN_ID"))  # type: ignore

    DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}/{DBNAME}"

except Exception as e:
    logger.error(f"Cant load .env data {e}", exc_info=True)
    raise RuntimeError
