from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

schedule_kb = ReplyKeyboardBuilder()
admit_decline_kb = ReplyKeyboardBuilder()
settings_kb = ReplyKeyboardBuilder()

schedule_kb.add(KeyboardButton(text="На сегодня"))
schedule_kb.add(KeyboardButton(text="На завтра"))
schedule_kb.add(KeyboardButton(text="На неделю"))
schedule_kb.add(KeyboardButton(text="На след. неделю"))
schedule_kb.add(KeyboardButton(text="Настройки"))
schedule_kb.adjust(2, 2, 1)

admit_decline_kb.add(KeyboardButton(text="Да"))
admit_decline_kb.add(KeyboardButton(text="Нет"))

settings_kb.add(KeyboardButton(text="Изменить мою группу"))
settings_kb.add(KeyboardButton(text="Оставить отзыв | Пожелания"))
settings_kb.add(KeyboardButton(text="Полезные ссылки"))
settings_kb.add(KeyboardButton(text="О нас"))
settings_kb.add(KeyboardButton(text="Вернуться"))
settings_kb.adjust(1, 1, 2, 1)
