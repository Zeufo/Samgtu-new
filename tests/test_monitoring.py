import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.monitoring import (
    changes_monitoring,
    schedule_diff_seeker,
    schedule_hash,
    week_changes_monitoring,
)


# ==========================================
# 1. ТЕСТ ХЕШИРОВАНИЯ
# ==========================================
def test_schedule_hash_deterministic(base_schedule):
    """Хеш должен быть одинаковым для одинаковых данных независимо от порядка ключей."""
    hash1 = schedule_hash(base_schedule)
    hash2 = schedule_hash(base_schedule)
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 32  # Длина MD5


# ==========================================
# 2. ТЕСТ ПОИСКА РАЗНИЦЫ В РАСПИСАНИИ (DIFF)
# ==========================================
@pytest.mark.asyncio
async def test_schedule_diff_seeker_detects_all_changes(base_schedule, updated_schedule):
    """Проверяем обнаружение добавлений, удалений и замен."""
    diff = await schedule_diff_seeker(base_schedule, updated_schedule)

    # Проверяем заголовок
    assert "🔔 Изменения в расписании:" in diff

    # Проверяем удаление (пара 1 в Пн)
    assert "❌ убрали" in diff
    assert "Высшая математика | ауд. 101" in diff

    # Проверяем замену (пара 2 в Пн)
    assert "✏️ Замена" in diff
    assert "Было:" in diff
    assert "Физика | ауд. 202" in diff
    assert "Стало:" in diff
    assert "Физика (ЛАБ) | ауд. 205" in diff

    # Проверяем добавление (пара 2 во Вт)
    assert "✳️ Добавили" in diff
    assert "Физкультура | ауд. Спортзал" in diff


@pytest.mark.asyncio
async def test_schedule_diff_seeker_no_changes(base_schedule):
    """Если расписания идентичны, в тексте не должно быть изменений."""
    diff = await schedule_diff_seeker(base_schedule, base_schedule)
    assert "❌ убрали" not in diff
    assert "✏️ Замена" not in diff
    assert "✳️ Добавили" not in diff


# ==========================================
# 3. ТЕСТ ПАРСИНГА ТЕКУЩЕЙ НЕДЕЛИ
# ==========================================
@pytest.mark.asyncio
async def test_week_changes_monitoring(html_week_page):
    """Проверяем, что неделя корректно извлекается из HTML."""
    mock_resp = AsyncMock()
    mock_resp.text.return_value = html_week_page

    # Эмулируем async with http_session.get(...)
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_resp

    with (
        patch("src.monitoring.WeekState") as mock_week_state,
        patch("asyncio.sleep", side_effect=[None, asyncio.CancelledError]),
    ):  # Прерываем вечный цикл
        try:
            await week_changes_monitoring(mock_session)
        except asyncio.CancelledError:
            pass

        assert mock_week_state.week == 2


# ==========================================
# 4. ТЕСТ ОСНОВНОГО ЦИКЛА МОНИТОРИНГА
# ==========================================
@pytest.mark.asyncio
async def test_changes_monitoring_when_schedule_changed(base_schedule, updated_schedule, mock_bot):
    """Сценарий: расписание изменилось -> обновляем БД и отправляем пуш пользователям."""
    group_id = 101
    old_hash = schedule_hash(base_schedule)

    # 1. Мокаем сервисы БД
    mock_schedule_service = AsyncMock()
    mock_schedule_service.get_groups_id.return_value = [(group_id,)]
    # Возвращаем старое расписание и старый хеш
    mock_schedule_service.get_schedule_and_hash.return_value = [(base_schedule, old_hash)]

    mock_user_service = AsyncMock()
    mock_user_service.get_all_users_in_group.return_value = [
        12345,
        67890,
    ]  # telegram user_ids

    # 2. Мокаем парсер (он возвращает НОВОЕ расписание)
    mock_parser = AsyncMock()
    mock_parser.parse.return_value = updated_schedule

    # 3. Мокаем сессию БД
    mock_db_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_db_session

    mock_http_session = MagicMock()

    # Патчим зависимости
    with (
        patch("src.monitoring.ScheduleService", return_value=mock_schedule_service),
        patch("src.monitoring.UserService", return_value=mock_user_service),
        patch("src.monitoring.HTTPScheduleParser", mock_parser),
        patch("src.monitoring.date_setter", AsyncMock()),
        patch("src.monitoring.NotifyUsers") as MockNotifyUsers,
        patch("src.monitoring.WeekState") as mock_week_state,
        patch(
            "asyncio.sleep",
            side_effect=[None, None, None, None, asyncio.CancelledError],
        ),
    ):
        mock_week_state.week = 1
        mock_notify_instance = AsyncMock()
        MockNotifyUsers.return_value = mock_notify_instance

        try:
            await changes_monitoring(mock_http_session, mock_session_maker, mock_bot)
        except asyncio.CancelledError:
            pass

        # ПРОВЕРКИ:
        # 1. БД обновилась новыми данными
        mock_schedule_service.update_schedule_in_monitoring.assert_called_once()
        call_args = mock_schedule_service.update_schedule_in_monitoring.call_args[0]
        assert call_args[1] == group_id
        assert call_args[2]["hash"] == schedule_hash(updated_schedule)

        # 2. Уведомление было отправлено
        mock_notify_instance.send.assert_called_once()
        users_sent, text_sent, _ = mock_notify_instance.send.call_args[0]
        assert users_sent == [12345, 67890]
        assert "🔔 Изменения в расписании:" in text_sent


@pytest.mark.asyncio
async def test_changes_monitoring_when_schedule_NOT_changed(base_schedule, mock_bot):
    """Сценарий: расписание НЕ изменилось -> обновляем только timestamp, пуш НЕ шлем."""
    group_id = 101
    current_hash = schedule_hash(base_schedule)

    mock_schedule_service = AsyncMock()
    mock_schedule_service.get_groups_id.return_value = [(group_id,)]
    mock_schedule_service.get_schedule_and_hash.return_value = [(base_schedule, current_hash)]

    mock_user_service = AsyncMock()
    mock_parser = AsyncMock()
    mock_parser.parse.return_value = base_schedule  # Возвращает то же самое!

    mock_db_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_db_session

    mock_http_session = MagicMock()

    with (
        patch("src.monitoring.ScheduleService", return_value=mock_schedule_service),
        patch("src.monitoring.UserService", return_value=mock_user_service),
        patch("src.monitoring.HTTPScheduleParser", mock_parser),
        patch("src.monitoring.date_setter", AsyncMock()),
        patch("src.monitoring.NotifyUsers") as MockNotifyUsers,
        patch("src.monitoring.WeekState") as mock_week_state,
        patch(
            "asyncio.sleep",
            side_effect=[None, None, None, None, asyncio.CancelledError],
        ),
    ):
        mock_week_state.week = 1
        mock_notify_instance = AsyncMock()
        MockNotifyUsers.return_value = mock_notify_instance

        try:
            await changes_monitoring(mock_http_session, mock_session_maker, mock_bot)
        except asyncio.CancelledError:
            pass

        # ПРОВЕРКИ:
        # 1. Вызов обновления был (обновили time), но без поля 'hash'
        mock_schedule_service.update_schedule_in_monitoring.assert_called_once()
        call_args = mock_schedule_service.update_schedule_in_monitoring.call_args[0]
        assert "hash" not in call_args[2]

        # 2. Уведомление НЕ отправлялось
        mock_notify_instance.send.assert_not_called()
