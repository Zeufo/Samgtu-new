import asyncio
import hashlib
import json
import time
import typing
from datetime import datetime

import aiogram
import aiohttp
import bs4
from loguru import logger

from config import PROXY_LINK, SITE_LINK, TZ_SAMARA, WeekState
from parse import HTTPScheduleParser
from services import NotifyUsers, ScheduleService, UserService, date_setter
from services.service_classes import ScheduleSnapshot

MONITORING_INTERVAL_SECONDS = 1200
GROUP_PARSE_DELAY_SECONDS = 0.3
CHANGE_RECHECK_DELAY_SECONDS = 2

# TODO:
# 1. Реализовать и навесить декоратор-предохранитель (Circuit Breaker) на HTTPScheduleParser.parse.
#    Если сервер вуза выдает 5 ошибок подряд — выбрасывать исключение и блокировать
#    новые запросы на 5 минут, чтобы не спамить впустую.
# 2. Покрыть ChangesProcess модульными тестами (особенно логику формирования diff и пакетного обновления).


async def week_changes_monitoring(http_session: aiohttp.ClientSession) -> bool:
    try:
        async with http_session.get(
            PROXY_LINK,
            params={"url": SITE_LINK},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            data = await response.text()
            soup = bs4.BeautifulSoup(data, "html.parser")
            select = soup.find("select", id="schedule_weektype_select")
            option = select.find("option", selected=True) if select else None  # type:ignore

            if option is None:
                logger.warning("Не удалось определить неделю: селектор недели не найден")
                return False

            WeekState.week = int(option["value"])  # type:ignore
            return True

    except Exception:
        logger.exception("Problem with week monitoring...")
        return False


def schedule_hash(schedule: list) -> str:
    raw = json.dumps(schedule, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def is_usable_schedule(schedule: typing.Any) -> bool:
    """Отсекает пустые и битые ответы парсера."""
    if not isinstance(schedule, list) or not schedule:
        return False

    return all(
        isinstance(day, dict) and day.get("day_name") and isinstance(day.get("lessons"), dict)
        for day in schedule
    )


def is_week_snapshot_consistent(
    week_before: int,
    week_after: int,
    time_before: datetime,
    time_after: datetime,
) -> bool:
    """Проверяет, что неделя и локальное время сняты по одну сторону границы."""
    local_boundary = time_before.isocalendar()[:2] != time_after.isocalendar()[:2]
    site_boundary = week_before != 0 and week_before != week_after
    return local_boundary == site_boundary


async def schedule_diff_seeker(old: list, new: list) -> str:
    # logger.debug(f"old is {old}")
    changes = []

    old_by_day = {
        day["day_name"]: {
            "lessons": {int(k): v for k, v in day["lessons"].items()},
            "week_day": day["week_day"],
        }
        for day in old
    }
    new_by_day = {
        day["day_name"]: {
            "lessons": {int(k): v for k, v in day["lessons"].items()},
            "week_day": day["week_day"],
        }
        for day in new
    }

    for day_name in sorted(set(old_by_day) | set(new_by_day)):
        old_day = old_by_day.get(day_name, {})
        new_day = new_by_day.get(day_name, {})

        old_lessons = old_day.get("lessons", {})
        new_lessons = new_day.get("lessons", {})
        week_day = new_day.get("week_day") or old_day.get("week_day")

        all_pair_numbers = set(old_lessons) | set(new_lessons)

        for pair_num in sorted(all_pair_numbers):
            old_lesson = old_lessons.get(pair_num)
            new_lesson = new_lessons.get(pair_num)

            if old_lesson is None and new_lesson is not None:
                changes.append(
                    f"✳️ Добавили\n<b>{day_name}, {week_day}</b>, пара {pair_num}\n"
                    f"⏱️<code>{new_lesson['время']}</code>\n"
                    f"📚{new_lesson['пара'].replace('ауд.', ' | ауд.')}\n"
                )
                changes.append("_________________________________\n")
            elif old_lesson is not None and new_lesson is None:
                changes.append(
                    f"❌ убрали\n <b>{day_name}, {week_day}</b>, пара {pair_num}\n"
                    f"⏱️<code>{old_lesson['время']}</code>\n"
                    f"📚{old_lesson['пара'].replace('ауд.', ' | ауд.')}\n"
                )

                changes.append("_________________________________\n")
            elif old_lesson != new_lesson:
                changes.append(
                    f"✏️ Замена\n<b>{day_name}, {week_day}</b>, пара {pair_num}\n"
                    f"Было: \n⏱️<code>{old_lesson['время'].replace('ауд.', ' | ауд.')}\n</code>📚{old_lesson['пара'].replace('ауд.', ' | ауд.')}\n"  # type:ignore
                    f"Стало: \n⏱️<code>{new_lesson['время']}\n</code>📚{new_lesson['пара'].replace('ауд.', ' | ауд.')}\n"  # type:ignore
                )
                changes.append("_________________________________\n")

    header = "🔔 Изменения в расписании:\n\n"
    return header + "\n".join(changes)


@typing.final
class ChangesProcess:
    def __init__(
        self,
        http_session: aiohttp.ClientSession,
        session_maker,
        bot: aiogram.Bot,
        notifications_enabled: bool = False,
    ) -> None:

        self.http_session = http_session
        self.session_maker = session_maker
        self.bot = bot
        self.notifications_enabled = notifications_enabled
        self.time_now = datetime.now(TZ_SAMARA)

    async def start_checking(self) -> None:
        logger.info(
            f"Мониторинг запущен: уведомления "
            f"{'включены' if self.notifications_enabled else 'отключены'}, "
            f"интервал {MONITORING_INTERVAL_SECONDS} с"
        )

        while True:
            logger.info("Мониторинг: начинаю цикл проверки")
            started = time.monotonic()

            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Мониторинг упал, продолжаю после паузы")
            finally:
                logger.info(
                    f"Мониторинг: цикл занял {time.monotonic() - started:.1f} с, "
                    f"следующий через {MONITORING_INTERVAL_SECONDS} с"
                )

            await asyncio.sleep(MONITORING_INTERVAL_SECONDS)

    async def run_once(self) -> None:
        week_before: int = WeekState.week
        time_before = datetime.now(TZ_SAMARA)

        week_ok = await week_changes_monitoring(self.http_session)

        week_after: int = WeekState.week
        time_now = datetime.now(TZ_SAMARA)

        if not week_ok:
            logger.warning("Не удалось получить неделю с сайта — пропускаю цикл")
            return

        if not is_week_snapshot_consistent(week_before, week_after, time_before, time_now):
            logger.warning(
                f"Несогласованные снимки недели: локально "
                f"{time_before.isocalendar()[:2]} -> {time_now.isocalendar()[:2]}, "
                f"сайт {week_before} -> {week_after}. Пропускаю цикл."
            )
            return

        week: int = week_after
        self.time_now = time_now

        logger.info(
            f"Снимок недели: сайт={week_after}, "
            f"время={time_now:%Y-%m-%d %H:%M:%S}"
        )

        for target_week, is_next in ((week, False), (week + 1, True)):
            logger.info(
                f"Проверяю неделю {target_week} "
                f"({'следующая' if is_next else 'текущая'})"
            )

            try:
                await self._schedule_changes_monitoring_cycle(target_week, is_next)
            except Exception:
                logger.exception(f"Ошибка цикла мониторинга для недели {target_week}")

    async def _find_groups_with_changes_and_process(
        self,
        groups_and_hashes: dict[int, ScheduleSnapshot],
        week: int,
        is_next: bool,
    ) -> tuple[list[dict], list[dict]]:
        to_update_full: list[dict] = []
        to_update_time: list[dict] = []
        skipped = 0
        failed = 0

        for group, snapshot in groups_and_hashes.items():
            try:
                await asyncio.sleep(GROUP_PARSE_DELAY_SECONDS)  # antiflood
                new_schd = await HTTPScheduleParser.parse(self.http_session, group, week)

                if not is_usable_schedule(new_schd):
                    logger.warning(
                        f"Пустое или некорректное расписание для группы {group} "
                        f"(неделя {week}), пропускаю"
                    )
                    skipped += 1
                    continue

                await date_setter(new_schd, is_next, self.time_now)
                new_hash = schedule_hash(new_schd)

                if new_hash != snapshot.hash:
                    await asyncio.sleep(CHANGE_RECHECK_DELAY_SECONDS)
                    recheck_schd = await HTTPScheduleParser.parse(self.http_session, group, week)

                    if not is_usable_schedule(recheck_schd):
                        logger.warning(
                            f"Повторная проверка вернула пустое расписание для группы {group} "
                            f"(неделя {week}), пропускаю изменение"
                        )
                        skipped += 1
                        continue

                    await date_setter(recheck_schd, is_next, self.time_now)
                    recheck_hash = schedule_hash(recheck_schd)

                    if recheck_hash == snapshot.hash:
                        logger.warning(
                            f"Повторная проверка для группы {group} вернула старое расписание — "
                            f"первый ответ был глюком"
                        )
                        new_schd = recheck_schd
                        new_hash = recheck_hash
                    elif recheck_hash != new_hash:
                        logger.warning(
                            f"Два запроса для группы {group} вернули разные расписания — "
                            f"пропускаю до следующего цикла"
                        )
                        skipped += 1
                        continue
                    else:
                        new_schd = recheck_schd

                if new_hash != snapshot.hash:
                    to_update_full.append(
                        {
                            "group_id": group,
                            "week_num": week,
                            "schedule_json": new_schd,
                            "hash": new_hash,
                            "old_hash": snapshot.hash,
                            "last_updated": int(self.time_now.timestamp()),
                            "last_updated_formated": self.time_now.strftime("%d %B %H:%M"),
                        }
                    )
                else:
                    to_update_time.append(
                        {
                            "group_id": group,
                            "week_num": week,
                            "last_updated": int(self.time_now.timestamp()),
                            "last_updated_formated": self.time_now.strftime("%d %B %H:%M"),
                        }
                    )

            except Exception:
                failed += 1
                logger.exception(f"Problem with parsing {group} at {week}")

        logger.info(
            f"Неделя {week}: проверено {len(groups_and_hashes)}, "
            f"изменено {len(to_update_full)}, без изменений {len(to_update_time)}, "
            f"пропущено {skipped}, ошибок {failed}"
        )

        return to_update_full, to_update_time

    async def _schedule_changes_monitoring_cycle(
        self,
        week: int,
        is_next: bool = False,
    ) -> None:
        async with self.session_maker() as session:
            schedule_service = ScheduleService(session)
            groups_and_hashes = (
                await schedule_service.get_every_groups_id_with_hashes_and_schedule_for_week(week)
            )

        if not groups_and_hashes:
            logger.info(f"Неделя {week}: группы не найдены, пропускаю")
            return

        to_update_full, to_update_time = await self._find_groups_with_changes_and_process(
            groups_and_hashes, week, is_next
        )

        try:
            async with self.session_maker() as session:
                async with session.begin():
                    schedule_service = ScheduleService(session)
                    await schedule_service.bulk_update_full_schedule(to_update_full, commit=False)
                    await schedule_service.bulk_update_only_time(to_update_time, commit=False)
        except Exception:
            logger.exception(f"Не удалось обновить расписание за неделю {week}")
            return

        logger.info(
            f"Неделя {week}: БД обновлена — полных {len(to_update_full)}, "
            f"только время {len(to_update_time)}"
        )

        if self.notifications_enabled and to_update_full:
            notify_users = NotifyUsers(self.bot)
            notified = 0
            no_users = 0
            notify_failed = 0

            for group_data in to_update_full:
                group_id = group_data["group_id"]
                old_schedule = groups_and_hashes[group_id].schedule
                new_schedule = group_data["schedule_json"]

                if not isinstance(old_schedule, list) or not isinstance(new_schedule, list):
                    logger.error(f"Некорректный тип расписания для группы {group_id}")
                    notify_failed += 1
                    continue

                diff = await schedule_diff_seeker(old_schedule, new_schedule)

                try:
                    async with self.session_maker() as session:
                        user_service = UserService(session)
                        users = await user_service.get_all_users_in_group(group_id)

                    if users:
                        await notify_users.send(users, diff, self.bot)
                        notified += 1
                    else:
                        no_users += 1
                except Exception:
                    notify_failed += 1
                    logger.exception(f"Не удалось отправить уведомление для группы {group_id}")

            logger.info(
                f"Неделя {week}: уведомления — отправлено {notified}, "
                f"без пользователей {no_users}, ошибок {notify_failed}"
            )
        elif to_update_full:
            logger.info(f"Неделя {week}: изменения есть, но уведомления отключены")


async def changes_monitoring(
    http_session: aiohttp.ClientSession,
    session_maker,
    bot: aiogram.Bot,
    NOTIFICATIONS_ENABLED: bool = False,
) -> None:
    await asyncio.sleep(10)
    local_week = int(WeekState.week)
    is_next = False
    while True:
        notify_users = NotifyUsers(bot)

        async with session_maker() as session:
            schedule_serv = ScheduleService(session)
            user_service = UserService(session)
            week: int = WeekState.week

            try:
                week: int = WeekState.week
                time_now = datetime.now(TZ_SAMARA)

                rows = await schedule_serv.get_groups_id(local_week)  # [(id1, id2, id3)]
                logger.debug(f"rows is... {rows}")

                if rows:
                    for group in rows:  # row here is group id
                        await asyncio.sleep(1)

                        row = group[0]
                        logger.debug(f"checking for {row}")

                        try:
                            new_schd = await HTTPScheduleParser.parse(http_session, row, local_week)
                        except Exception as e:
                            logger.warning(f"Problem with parsing {row} at {local_week}... {e}")
                            continue

                        await date_setter(new_schd, is_next, time_now)
                        new_hash = schedule_hash(new_schd)

                        data = await schedule_serv.get_schedule_and_hash(
                            local_week, row
                        )  # [( [{}], 'str')]

                        old_schd = data[0][0]  # type:ignore
                        old_hash = data[0][1]  # type:ignore

                        if (
                            old_schd is None or old_hash is None
                        ):  # Эт кстати очень плохо. в начале года руинит если расписания нет
                            logger.info(f"Schedule is None for  {row} at {week}... why?")
                            if new_schd:
                                to_update = {
                                    "schedule_json": new_schd,
                                    "hash": new_hash,
                                    "last_updated": int(time_now.timestamp()),
                                    "last_updated_formated": time_now.strftime("%d %B %H:%M"),
                                }

                                await schedule_serv.update_schedule_in_monitoring(
                                    local_week, row, to_update
                                )
                                logger.debug("Updated")

                                if NOTIFICATIONS_ENABLED:
                                    logger.info(f"NOTIFY {row} group")
                                    changes = "Обнаружено изменение в расписании!\nПохоже поставили пары.\nРазраб криворукий, поэтому, пожалуйста, проверьте сами.\n /week\n/nextweek"
                                    users = await user_service.get_all_users_in_group(row)
                                    if users and NOTIFICATIONS_ENABLED:
                                        await notify_users.send(users, changes, bot)

                            continue

                        if new_hash == old_hash:
                            update = {
                                "last_updated_formated": time_now.strftime("%d %B %H:%M"),
                                "last_updated": int(time_now.timestamp()),
                            }
                            await schedule_serv.update_schedule_in_monitoring(
                                local_week, row, update
                            )
                            continue

                        else:
                            logger.warning(f"Schedule changed for {row}... starting alarm")

                            changes = await schedule_diff_seeker(old_schd, new_schd)

                            to_update = {
                                "schedule_json": new_schd,
                                "hash": new_hash,
                                "last_updated": int(time_now.timestamp()),
                                "last_updated_formated": time_now.strftime("%d %B %H:%M"),
                            }

                            await schedule_serv.update_schedule_in_monitoring(
                                local_week, row, to_update
                            )
                            logger.debug("Updated")

                            if NOTIFICATIONS_ENABLED:
                                users = await user_service.get_all_users_in_group(row)
                                logger.info(f"users for notify is {users}")
                                if users and NOTIFICATIONS_ENABLED:
                                    await notify_users.send(users, changes, bot)

                        await asyncio.sleep(2)

                if local_week == WeekState.week:
                    local_week += 1
                    is_next = True
                else:
                    local_week = WeekState.week
                    is_next = False
            except asyncio.CancelledError:
                raise

            except Exception as e:
                logger.warning(f"Problem with monitoring... {e}")
                await asyncio.sleep(60)  # 60

        await asyncio.sleep(1800)
