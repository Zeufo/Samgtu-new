import asyncio
from copy import deepcopy
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config import TZ_SAMARA
from services import date_setter
from services.service_classes import ScheduleSnapshot
from utils.monitoring import (
    ChangesProcess,
    changes_monitoring,
    is_week_snapshot_consistent,
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
    assert "Высшая математика" in diff
    assert "ауд. 101" in diff

    # Проверяем замену (пара 2 в Пн)
    assert "✏️ Замена" in diff
    assert "Было:" in diff
    assert "Физика" in diff
    assert "ауд. 202" in diff
    assert "Стало:" in diff
    assert "Физика (ЛАБ)" in diff
    assert "ауд. 205" in diff

    # Проверяем добавление (пара 2 во Вт)
    assert "✳️ Добавили" in diff
    assert "Физкультура" in diff
    assert "ауд. Спортзал" in diff


@pytest.mark.asyncio
async def test_schedule_diff_seeker_no_changes(base_schedule):
    """Если расписания идентичны, в тексте не должно быть изменений."""
    diff = await schedule_diff_seeker(base_schedule, base_schedule)
    assert "❌ убрали" not in diff
    assert "✏️ Замена" not in diff
    assert "✳️ Добавили" not in diff


@pytest.mark.asyncio
async def test_schedule_diff_seeker_detects_removed_day(base_schedule):
    """Если из расписания пропал целый день, это тоже должно попасть в diff."""
    new_schedule = [base_schedule[0]]  # убираем вторник

    diff = await schedule_diff_seeker(base_schedule, new_schedule)

    assert "❌ убрали" in diff
    assert "Вторник" in diff
    assert "История" in diff
    assert "ауд. 303" in diff


# ==========================================
# 2.5. ГРАНИЦА ДНЯ / НЕДЕЛИ
# ==========================================
@pytest.mark.asyncio
async def test_no_false_positive_when_day_changes_within_week(base_schedule):
    """Проверка началась в 23:59, день сменился, но неделя та же.

    `date_setter` считает даты от начала текущей недели, поэтому переход
    через полночь внутри одной недели не меняет хеш — ложного срабатывания нет.
    """
    before = deepcopy(base_schedule)
    after = deepcopy(base_schedule)

    await date_setter(before, False, datetime(2025, 9, 1, 23, 59, tzinfo=TZ_SAMARA))
    await date_setter(after, False, datetime(2025, 9, 2, 0, 1, tzinfo=TZ_SAMARA))

    assert schedule_hash(before) == schedule_hash(after)


@pytest.mark.asyncio
async def test_week_boundary_changes_hash(base_schedule):
    """На границе недели даты сдвигаются на 7 дней — хеш меняется.

    Если `WeekState.week` не успел обновиться, сравнение пойдёт со старой
    записью, и это даст ложное срабатывание по всем группам.
    """
    sunday = deepcopy(base_schedule)
    monday = deepcopy(base_schedule)

    await date_setter(sunday, False, datetime(2025, 9, 7, 23, 59, tzinfo=TZ_SAMARA))
    await date_setter(monday, False, datetime(2025, 9, 8, 0, 1, tzinfo=TZ_SAMARA))

    assert schedule_hash(sunday) != schedule_hash(monday)


@pytest.mark.parametrize(
    ("week_before", "week_after", "time_before", "time_after", "expected"),
    [
        # Ни одна из границ не пересечена
        (1, 1, datetime(2025, 9, 1, 12, 0, tzinfo=TZ_SAMARA), datetime(2025, 9, 1, 12, 1, tzinfo=TZ_SAMARA), True),
        # Только локальная неделя сменилась
        (1, 1, datetime(2025, 9, 7, 23, 59, tzinfo=TZ_SAMARA), datetime(2025, 9, 8, 0, 1, tzinfo=TZ_SAMARA), False),
        # Только неделя сайта сменилась
        (1, 2, datetime(2025, 9, 1, 12, 0, tzinfo=TZ_SAMARA), datetime(2025, 9, 1, 12, 1, tzinfo=TZ_SAMARA), False),
        # Обе границы пересечены одновременно
        (1, 2, datetime(2025, 9, 7, 23, 59, tzinfo=TZ_SAMARA), datetime(2025, 9, 8, 0, 1, tzinfo=TZ_SAMARA), True),
        # Первый запуск: WeekState ещё 0
        (0, 1, datetime(2025, 9, 1, 12, 0, tzinfo=TZ_SAMARA), datetime(2025, 9, 1, 12, 1, tzinfo=TZ_SAMARA), True),
    ],
)
def test_week_snapshot_consistency(
    week_before, week_after, time_before, time_after, expected
):
    assert (
        is_week_snapshot_consistent(week_before, week_after, time_before, time_after)
        is expected
    )


@pytest.mark.asyncio
async def test_changes_process_no_false_positive_at_midnight(base_schedule, mock_bot):
    """Проход сравнения, начатый в 23:59, не должен давать изменений."""
    start_time = datetime(2025, 9, 1, 23, 59, tzinfo=TZ_SAMARA)

    stored = deepcopy(base_schedule)
    await date_setter(stored, False, start_time)

    mock_parser = AsyncMock()
    mock_parser.parse.return_value = deepcopy(base_schedule)

    process = ChangesProcess(MagicMock(), MagicMock(), mock_bot, notifications_enabled=False)
    process.time_now = start_time

    groups = {
        101: ScheduleSnapshot(hash=schedule_hash(stored), schedule=stored),
    }

    with (
        patch("utils.monitoring.HTTPScheduleParser", mock_parser),
        patch("asyncio.sleep", AsyncMock()),
    ):
        to_update_full, to_update_time = await process._find_groups_with_changes_and_process(
            groups, week=1, is_next=False
        )

    assert to_update_full == []
    assert len(to_update_time) == 1
    assert to_update_time[0]["group_id"] == 101


@pytest.mark.asyncio
async def test_changes_process_accepts_change_after_two_identical_responses(
    base_schedule, updated_schedule, mock_bot
):
    """Изменение принимается, если повторный запрос вернул то же самое."""
    time_now = datetime(2025, 9, 1, 12, 0, tzinfo=TZ_SAMARA)
    stored = deepcopy(base_schedule)
    await date_setter(stored, False, time_now)

    mock_parser = AsyncMock()
    mock_parser.parse.side_effect = [
        deepcopy(updated_schedule),
        deepcopy(updated_schedule),
    ]

    process = ChangesProcess(MagicMock(), MagicMock(), mock_bot, notifications_enabled=False)
    process.time_now = time_now

    groups = {101: ScheduleSnapshot(hash=schedule_hash(stored), schedule=stored)}

    with (
        patch("utils.monitoring.HTTPScheduleParser", mock_parser),
        patch("asyncio.sleep", AsyncMock()),
    ):
        to_update_full, to_update_time = await process._find_groups_with_changes_and_process(
            groups, week=1, is_next=False
        )

    assert len(to_update_full) == 1
    assert to_update_full[0]["group_id"] == 101
    assert to_update_full[0]["old_hash"] == schedule_hash(stored)
    assert to_update_time == []
    assert mock_parser.parse.await_count == 2


@pytest.mark.asyncio
async def test_changes_process_ignores_glitch_if_recheck_matches_old(
    base_schedule, updated_schedule, mock_bot
):
    """Если второй запрос вернул старое расписание, первый ответ — глюк."""
    time_now = datetime(2025, 9, 1, 12, 0, tzinfo=TZ_SAMARA)
    stored = deepcopy(base_schedule)
    await date_setter(stored, False, time_now)

    mock_parser = AsyncMock()
    mock_parser.parse.side_effect = [
        deepcopy(updated_schedule),
        deepcopy(base_schedule),
    ]

    process = ChangesProcess(MagicMock(), MagicMock(), mock_bot, notifications_enabled=False)
    process.time_now = time_now

    groups = {101: ScheduleSnapshot(hash=schedule_hash(stored), schedule=stored)}

    with (
        patch("utils.monitoring.HTTPScheduleParser", mock_parser),
        patch("asyncio.sleep", AsyncMock()),
    ):
        to_update_full, to_update_time = await process._find_groups_with_changes_and_process(
            groups, week=1, is_next=False
        )

    assert to_update_full == []
    assert len(to_update_time) == 1
    assert mock_parser.parse.await_count == 2


@pytest.mark.asyncio
async def test_changes_process_skips_inconsistent_responses(
    base_schedule, updated_schedule, mock_bot
):
    """Два разных ответа подряд — непонятно, чему верить, пропускаем."""
    time_now = datetime(2025, 9, 1, 12, 0, tzinfo=TZ_SAMARA)
    stored = deepcopy(base_schedule)
    await date_setter(stored, False, time_now)

    other = deepcopy(base_schedule)
    other[0]["lessons"]["1"]["пара"] = "Другая пара ауд. 999"

    mock_parser = AsyncMock()
    mock_parser.parse.side_effect = [deepcopy(updated_schedule), other]

    process = ChangesProcess(MagicMock(), MagicMock(), mock_bot, notifications_enabled=False)
    process.time_now = time_now

    groups = {101: ScheduleSnapshot(hash=schedule_hash(stored), schedule=stored)}

    with (
        patch("utils.monitoring.HTTPScheduleParser", mock_parser),
        patch("asyncio.sleep", AsyncMock()),
    ):
        to_update_full, to_update_time = await process._find_groups_with_changes_and_process(
            groups, week=1, is_next=False
        )

    assert to_update_full == []
    assert to_update_time == []


@pytest.mark.asyncio
async def test_changes_process_skips_empty_schedule(base_schedule, mock_bot):
    """Пустой ответ парсера не должен стирать расписание."""
    time_now = datetime(2025, 9, 1, 12, 0, tzinfo=TZ_SAMARA)
    stored = deepcopy(base_schedule)
    await date_setter(stored, False, time_now)

    mock_parser = AsyncMock()
    mock_parser.parse.return_value = []

    process = ChangesProcess(MagicMock(), MagicMock(), mock_bot, notifications_enabled=False)
    process.time_now = time_now

    groups = {101: ScheduleSnapshot(hash=schedule_hash(stored), schedule=stored)}

    with (
        patch("utils.monitoring.HTTPScheduleParser", mock_parser),
        patch("asyncio.sleep", AsyncMock()),
    ):
        to_update_full, to_update_time = await process._find_groups_with_changes_and_process(
            groups, week=1, is_next=False
        )

    assert to_update_full == []
    assert to_update_time == []
    assert mock_parser.parse.await_count == 1


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

    with patch("utils.monitoring.WeekState") as mock_week_state:
        result = await week_changes_monitoring(mock_session)

    assert result is True
    assert mock_week_state.week == 2


@pytest.mark.asyncio
async def test_week_changes_monitoring_returns_false_without_selector():
    """Если селектора нет, неделя не обновляется и возвращается False."""
    mock_resp = AsyncMock()
    mock_resp.text.return_value = "<html><body><p>no selector</p></body></html>"

    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_resp

    with patch("utils.monitoring.WeekState") as mock_week_state:
        mock_week_state.week = 1
        result = await week_changes_monitoring(mock_session)

    assert result is False
    assert mock_week_state.week == 1


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

    # 3. Мокаем сессию БД (async context manager)
    mock_db_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_http_session = MagicMock()

    # Патчим зависимости
    with (
        patch("utils.monitoring.ScheduleService", return_value=mock_schedule_service),
        patch("utils.monitoring.UserService", return_value=mock_user_service),
        patch("utils.monitoring.HTTPScheduleParser", mock_parser),
        patch("utils.monitoring.date_setter", AsyncMock()),
        patch("utils.monitoring.NotifyUsers") as MockNotifyUsers,
        patch("utils.monitoring.WeekState") as mock_week_state,
        patch(
            "asyncio.sleep",
            side_effect=[None, None, None, None, asyncio.CancelledError],
        ),
    ):
        mock_week_state.week = 1
        mock_notify_instance = AsyncMock()
        MockNotifyUsers.return_value = mock_notify_instance

        try:
            # NOTIFICATIONS_ENABLED=True, иначе ветка отправки пуша не выполняется
            await changes_monitoring(mock_http_session, mock_session_maker, mock_bot, True)
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
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_http_session = MagicMock()

    with (
        patch("utils.monitoring.ScheduleService", return_value=mock_schedule_service),
        patch("utils.monitoring.UserService", return_value=mock_user_service),
        patch("utils.monitoring.HTTPScheduleParser", mock_parser),
        patch("utils.monitoring.date_setter", AsyncMock()),
        patch("utils.monitoring.NotifyUsers") as MockNotifyUsers,
        patch("utils.monitoring.WeekState") as mock_week_state,
        patch(
            "asyncio.sleep",
            # 10 + 1 + 1800 -> и на следующей итерации sleep(1) отменяет цикл
            side_effect=[None, None, None, asyncio.CancelledError],
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
