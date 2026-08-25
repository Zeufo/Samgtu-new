from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def base_schedule():
    """Базовое расписание (исходное)."""
    return [
        {
            "day_name": "Понедельник",
            "week_day": "01.09.2025",
            "lessons": {
                "1": {"время": "08:30-10:00", "пара": "Высшая математика ауд. 101"},
                "2": {"время": "10:15-11:45", "пара": "Физика ауд. 202"},
            },
        },
        {
            "day_name": "Вторник",
            "week_day": "02.09.2025",
            "lessons": {
                "1": {"время": "08:30-10:00", "пара": "История ауд. 303"},
            },
        },
    ]


@pytest.fixture
def updated_schedule():
    """Расписание с изменениями:

    - В пн убрали 1 пару
    - В пн заменили 2 пару
    - Во вт добавили 2 пару
    """
    return [
        {
            "day_name": "Понедельник",
            "week_day": "01.09.2025",
            "lessons": {
                # пара 1 убрана
                "2": {
                    "время": "10:15-11:45",
                    "пара": "Физика (ЛАБ) ауд. 205",
                },  # замена
            },
        },
        {
            "day_name": "Вторник",
            "week_day": "02.09.2025",
            "lessons": {
                "1": {"время": "08:30-10:00", "пара": "История ауд. 303"},
                "2": {
                    "время": "10:15-11:45",
                    "пара": "Физкультура ауд. Спортзал",
                },  # добавлена
            },
        },
    ]


@pytest.fixture
def html_week_page():
    """HTML страница с селектором недели."""
    return """
    <html>
        <body>
            <select id="schedule_weekttype_select">
                <option value="1">1 неделя</option>
                <option value="2" selected="selected">2 неделя</option>
                <option value="3">3 неделя</option>
            </select>
        </body>
    </html>
    """


@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot
