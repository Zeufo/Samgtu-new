import json
import re
from zoneinfo import ZoneInfo

import bs4

TZ_SAMARA = ZoneInfo("Europe/Samara")


def faculties_formatter(raw) -> list:

    soup = bs4.BeautifulSoup(raw, "lxml")
    faculties = soup.find("select", class_="schedule-selects")

    if faculties:
        faculties = faculties.find_all("option")

        faculties_id = []
        for i in faculties:
            key = i.get("value")

            if key == "" or key is None:
                continue

            key = int(str(key))

            faculties_id.append(key)  # all faculties keys

        return faculties_id

    else:
        raise RuntimeError


async def clean_schedule(response):
    raw_text = await response.text()

    try:
        json_start = raw_text.find("{")
        if json_start != -1:
            clean_json_str = raw_text[json_start:]
            data = json.loads(clean_json_str)
        else:
            return []

    except json.JSONDecodeError as e:
        return []

    cleanr = re.compile("<.*?>")

    def clean_text(text):
        if not text:
            return ""
        text = re.sub(cleanr, " ", text)
        text = text.replace("^", "")
        text = text.replace("\xa0", " ").strip()
        return text

    days = data.get("wd", {})

    schedule = []
    temp = {}

    i = 0

    for day_id, day_data in days.items():
        day_name = day_data.get("Name")
        times = day_data.get("at", {})

        temp = {"day_name": day_name}
        temp["lessons"] = {}

        less = 1  # lesson
        for time_id, time_info in times.items():
            cells = time_info.get("Cells", [])

            if not cells:
                continue

            for cell in cells:
                time_name = clean_text(time_info.get("Name"))
                content = clean_text(cell.get("CellName", ""))

                if content is not None:
                    temp["lessons"][less] = {
                        "пара": content.replace("№ ", "№")
                        .replace("лекция", "(лекция)")
                        .replace("практические занятия", "(практика)")
                        .replace("лабораторные занятия", "(лаба)")
                        .replace("аудитория", "ауд.")
                        .replace(",", "")
                        .replace("корпус", "кор.")
                        .replace("экзамен", "(экз.)"),
                        "время": time_name.replace(" -", "-").replace(" ", ":"),
                    }

                less = less + 1
        i += 1

        schedule.append(temp)
    return schedule


async def parse_groups_formatter():
    groups_info = []

    async def add_groups_to_info(
        groups_from_faculty: list, course: int, faculty: int, need_return=False
    ):
        nonlocal groups_info

        if need_return:
            return groups_info

        for group in groups_from_faculty:
            group["Name"] = group["Name"].rsplit(None, 1)[-1]
            group["Name"] = group["Name"].replace("–", "")
            group["Name"] = group["Name"][2:].upper()

            if (
                len(group["Name"]) < 5
                or len(group["Name"].translate(str.maketrans("", "", "1234567890"))) < 2
            ):
                del group
                continue

            if group["Name"] is None:
                del group
                continue

            group["course"] = course
            group["ID"] = int(group["ID"])

            to_insert = [group["ID"], group["Name"], faculty, group["course"]]

            groups_info.append(to_insert)

    return add_groups_to_info
