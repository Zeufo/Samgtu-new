from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

schedule_kb = ReplyKeyboardBuilder()
admit_decline_kb = ReplyKeyboardBuilder()

schedule_kb.add(KeyboardButton(text="На сегодня"))
schedule_kb.add(KeyboardButton(text="На завтра"))
schedule_kb.add(KeyboardButton(text="На неделю"))
schedule_kb.add(KeyboardButton(text="На след. неделю"))
schedule_kb.add(KeyboardButton(text="Изменить мою группу"))
schedule_kb.adjust(2, 2, 1)

admit_decline_kb.add(KeyboardButton(text="Да"))
admit_decline_kb.add(KeyboardButton(text="Нет"))
